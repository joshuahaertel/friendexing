import asyncio
import os
from asyncio import Future
from base64 import b64encode
from io import BytesIO
from math import log, ceil
from typing import Optional, Tuple, List
from xml.etree.ElementTree import Element

import aiohttp
from PIL import Image
from cryptography.fernet import Fernet
from defusedxml import ElementTree

from games.models import Batch, ImageModel

SUBSTRING = b'<input type="hidden" name="params" value="'
SUBSTRING_LEN = len(SUBSTRING)

GET_LOGIN_URL = (
    'https://www.familysearch.org/auth/familysearch/login'
)
POST_LOGIN_URL = (
    'https://ident.familysearch.org/cis-web/oauth2/v3/authorization'
)
MANIFEST_NAMESPACES = {
    'default': 'http://www.w3.org/2005/Atom',
    'indexing': 'http://familysearch.org/idx',
}
METADATA_NAMESPACES = {
    'default': 'http://schemas.microsoft.com/deepzoom/2009',
}


# todo: request timeouts

class FamilySearchJob:
    def __init__(self, batch_id: str):
        self.batch_id = batch_id
        self.future: Future[Batch] = asyncio.Future()

    async def run(self):
        family_search_user = get_family_search_user()
        await family_search_user.queue.put(self)
        return await self.future


class FamilySearchUser:
    def __init__(self):
        fernet = Fernet(os.environb[b'FERNET_KEY'])
        encrypted_username = os.environb[b'FAMILY_SEARCH_USERNAME']
        encrypted_password = os.environb[b'FAMILY_SEARCH_PASSWORD']
        self.username = fernet.decrypt(encrypted_username).decode()
        self.password = fernet.decrypt(encrypted_password).decode()
        self.json_token = ''
        self.queue: asyncio.Queue[FamilySearchJob] = asyncio.Queue()
        self.session: Optional[aiohttp.ClientSession] = None

    async def run(self):
        async with aiohttp.ClientSession() as self.session:
            await self.login()
            while True:
                job = await self.queue.get()
                await self.run_job(job)

    async def login(self):
        csrf_token = await self.get_csrf_token()
        await self.get_json_token(csrf_token)

    async def get_csrf_token(self):
        async with self.session.get(GET_LOGIN_URL) as resp:
            html = await resp.read()
            value_start_index = html.index(SUBSTRING) + SUBSTRING_LEN
            end_index = html.index(b'"', value_start_index)
            csrf_token_bytes = html[value_start_index:end_index]
            return csrf_token_bytes.decode()

    async def get_json_token(self, csrf_token):
        data = {
            'userName': self.username,
            'password': self.password,
            'params': csrf_token,
        }
        async with self.session.post(POST_LOGIN_URL, data=data) as resp:
            _ = await resp.read()
            self.json_token = resp.history[1].cookies['fssessionid'].value

    async def run_job(self, job: FamilySearchJob):
        async with self.session.get(
                f'https://sg30p0.familysearch.org'
                f'/service/indexing/project/images'
                f'?batchid={job.batch_id}&actualimagelink=true',
                headers={'authorization': f'bearer {self.json_token}'}
        ) as manifest_response:
            manifest_xml_text = await manifest_response.text()
        manifest_element: Element = ElementTree.fromstring(manifest_xml_text)
        images_xml = manifest_element.findall(
            './default:entry[@indexing:rel="relations/image"]',
            namespaces=MANIFEST_NAMESPACES,
        )
        image_futures = []
        for image_xml in images_xml:
            image_id = image_xml.get('{http://familysearch.org/idx}uuid')
            image_metadata_url = image_xml.find(
                './default:link[@rel="relations/image/deepzoom"]',
                MANIFEST_NAMESPACES,
            )
            image_metadata_url = image_metadata_url.get('href')
            thumbnail_element = image_xml.find(
                './default:link[@rel="relations/image/thumbnail"]',
                MANIFEST_NAMESPACES,
            )
            thumbnail_url = thumbnail_element.get('href')
            family_search_image = FamilySearchImage(
                image_id,
                image_metadata_url,
                thumbnail_url,
            )
            image_futures.append(
                asyncio.ensure_future(
                    family_search_image.fetch(self.session)
                )
            )
            await asyncio.sleep(0)
        family_search_image_tasks, _ = await asyncio.wait(image_futures)

        image_models: List[ImageModel] = []
        family_search_image_task: asyncio.Task[FamilySearchImage]
        for family_search_image_task in family_search_image_tasks:
            family_search_image = family_search_image_task.result()
            image_model = family_search_image.as_image_model()
            image_models.append(image_model)
        batch = Batch(job.batch_id, image_models)
        job.future.set_result(batch)


class FamilySearchImage:
    def __init__(self, image_id, image_metadata_url: str, thumbnail_url):
        self.image_id = image_id
        self.image_metadata_url = image_metadata_url
        self.thumbnail_url = thumbnail_url
        self.thumbnail: Optional[RawImage] = None
        self.full_size_image: Optional[RawImage] = None

    async def fetch(self, client):
        await asyncio.gather(
            self.get_thumbnail(client),
            self.get_full_size_image(client),
        )
        return self

    async def get_thumbnail(self, client: aiohttp.ClientSession):
        self.thumbnail = await get_image(self.thumbnail_url, client)

    async def get_full_size_image(self, client):
        async with client.get(self.image_metadata_url) as metadata_response:
            metadata_xml_text = await metadata_response.text()
        image_metadata_element: Element = ElementTree.fromstring(
            metadata_xml_text
        )
        tile_size = int(image_metadata_element.get('TileSize'))
        image_format = image_metadata_element.get('Format')
        tile_overlap = int(image_metadata_element.get('Overlap'))
        size_element = image_metadata_element.find(
            './default:Size',
            namespaces=METADATA_NAMESPACES,
        )
        image_width = int(size_element.get('Width'))
        image_height = int(size_element.get('Height'))
        max_x_tiles = (image_width // tile_size) + 1
        max_y_tiles = (image_height // tile_size) + 1
        max_dimension_size = max(image_width, image_height)
        zoom_factor = ceil(log(max_dimension_size, 2))
        tile_url_template = self.image_metadata_url.replace(
            'image.xml',
            f'image_files/{zoom_factor}/{{x}}_{{y}}.{image_format}',
        )
        full_image = Image.new(
            mode='L',
            size=(image_width, image_height),
            color=None,
        )
        coroutines = []
        for y_index in range(max_y_tiles):
            top_overlap = y_index != 0
            for x_index in range(max_x_tiles):
                left_overlap = x_index != 0
                tile_url = tile_url_template.format(
                    x=x_index,
                    y=y_index,
                )
                tile = ImageTile(
                    url=tile_url,
                    tile_coordinate=self.get_coordinates(
                        x_index,
                        y_index,
                        tile_size,
                        tile_overlap,
                        top_overlap,
                        left_overlap,
                    ),
                    full_image=full_image,
                    client=client,
                )
                coroutines.append(
                    asyncio.ensure_future(
                        tile.process()
                    )
                )
                await asyncio.sleep(0)
        await asyncio.gather(*coroutines)
        # todo: thread pool?
        full_image_bytes = BytesIO()
        full_image.save(full_image_bytes, 'jpeg')
        self.full_size_image = RawImage(
            image=full_image_bytes.getvalue(),
            content_type='img/jpeg',
        )

    @staticmethod
    def get_coordinates(
            x_index,
            y_index,
            tile_size,
            tile_overlap,
            top_overlap,
            left_overlap,
    ):
        if left_overlap:
            x_shift = -tile_overlap
        else:
            x_shift = 0
        x_coordinate = x_index * tile_size + x_shift

        if top_overlap:
            y_shift = -tile_overlap
        else:
            y_shift = 0
        y_coordinate = y_index * tile_size + y_shift

        return x_coordinate, y_coordinate

    async def save_all(self):
        await self.save_image_html()
        await self.save_thumbnail_html()
        await self.save_image_jpeg()
        await self.save_thumbnail_jpeg()

    async def save_image_html(self):
        with open(f'{self.image_id}_main.html', mode='w') as html_file:
            html_file.write(f"""
            <html>
                <body>
                    <img src="{self.full_size_image.as_html_src()}">
                </body>
            </html>""")

    async def save_thumbnail_html(self):
        with open(f'{self.image_id}_thumbnail.html', mode='w') as html_file:
            html_file.write(f"""
            <html>
                <body>
                    <img src="{self.thumbnail.as_html_src()}">
                </body>
            </html>""")

    async def save_image_jpeg(self):
        with open(f'{self.image_id}_main.jpg', mode='wb') as image_file:
            image_file.write(self.full_size_image.image_bytes)

    async def save_thumbnail_jpeg(self):
        with open(f'{self.image_id}_thumbnail.jpg', mode='wb') as image_file:
            image_file.write(self.thumbnail.image_bytes)

    def as_image_model(self):
        return ImageModel(
            self.image_id,
            self.full_size_image.image_bytes,
            self.thumbnail.image_bytes,
        )


async def get_image(image_url, client):
    async with client.get(image_url) as image_response:
        image_bytes = await image_response.read()
        content_type = image_response.headers.get(
            'content-type',
            # Guess this is a jpeg
            'img/jpeg',
        )
        return RawImage(image_bytes, content_type)


class RawImage:
    def __init__(self, image: bytes, content_type: str):
        self.image_bytes = image
        self.content_type = content_type

    def as_html_src(self):
        encoded_image = b64encode(self.image_bytes)
        return (
                b'data:'
                + self.content_type.encode()
                + b';base64,'
                + encoded_image
        ).decode()


class ImageTile:
    def __init__(
            self,
            url: str,
            tile_coordinate: Tuple[int, int],
            full_image: Image.Image,
            client: aiohttp.ClientSession,
    ) -> None:
        self.url = url
        self.tile_coordinate = tile_coordinate
        self.full_image = full_image
        self.client = client

    async def process(self):
        image = await get_image(self.url, self.client)
        tile_pillow_image: Image.Image = Image.open(BytesIO(image.image_bytes))
        # todo: thread pool?
        self.full_image.paste(
            tile_pillow_image,
            self.tile_coordinate,
        )


_family_search_user: Optional[FamilySearchUser] = None


def get_family_search_user():
    global _family_search_user
    if not _family_search_user:
        _family_search_user = FamilySearchUser()
        asyncio.create_task(_family_search_user.run())
    return _family_search_user
