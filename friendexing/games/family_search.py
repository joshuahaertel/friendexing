import os

import aiohttp
from cryptography.fernet import Fernet

SUBSTRING = b'<input type="hidden" name="params" value="'
SUBSTRING_LEN = len(SUBSTRING)

GET_LOGIN_URL = (
    'https://www.familysearch.org/auth/familysearch/login'
)
POST_LOGIN_URL = (
    'https://ident.familysearch.org/cis-web/oauth2/v3/authorization'
)


class FamilySearchUser:
    def __init__(self):
        fernet = Fernet(os.environb[b'FERNET_KEY'])
        encrypted_username = os.environb[b'FAMILY_SEARCH_USERNAME']
        encrypted_password = os.environb[b'FAMILY_SEARCH_PASSWORD']
        self.username = fernet.decrypt(encrypted_username).decode()
        self.password = fernet.decrypt(encrypted_password).decode()
        self.json_token = ''

    async def run(self):
        async with aiohttp.ClientSession() as session:
            await self.login(session)

    async def login(self, session):
        csrf_token = await self.get_csrf_token(session)
        await self.get_json_token(session, csrf_token)

    @staticmethod
    async def get_csrf_token(session):
        async with session.get(GET_LOGIN_URL) as resp:
            html = await resp.read()
            value_start_index = html.index(SUBSTRING) + SUBSTRING_LEN
            end_index = html.index(b'"', value_start_index)
            csrf_token_bytes = html[value_start_index:end_index]
            return csrf_token_bytes.decode()

    async def get_json_token(self, session, csrf_token):
        data = {
            'userName': self.username,
            'password': self.password,
            'params': csrf_token,
        }
        async with session.post(POST_LOGIN_URL, data=data) as resp:
            _ = await resp.read()
            self.json_token = resp.history[1].cookies['fssessionid'].value
