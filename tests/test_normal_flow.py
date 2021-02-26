import logging
import os
from functools import partial
from time import sleep
from typing import Callable, List, Tuple
from unittest import TestCase

from selenium import webdriver
from selenium.webdriver import DesiredCapabilities, ActionChains
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait

LOGGER = logging.getLogger(__name__)


class TestNormalFlow(TestCase):
    chrome_driver: WebDriver
    firefox_driver: WebDriver

    @classmethod
    def setUpClass(cls) -> None:
        chromium_address = os.getenv(
            'CHROMIUM_ADDRESS',
            'http://chromium:4444',
        )
        cls.chrome_driver = cls.connect_to_web_driver(
            connect_command=partial(
                webdriver.Remote,
                command_executor=f'{chromium_address}/wd/hub',
                desired_capabilities=DesiredCapabilities.CHROME,
            )
        )
        firefox_address = os.getenv(
            'FIREFOX_ADDRESS',
            'http://firefox:4444',
        )
        cls.firefox_driver = cls.connect_to_web_driver(
            connect_command=partial(
                webdriver.Remote,
                command_executor=f'{firefox_address}/wd/hub',
                desired_capabilities=DesiredCapabilities.FIREFOX,
            )
        )
        cls.addClassCleanup(cls.chrome_driver.quit)
        cls.addClassCleanup(cls.firefox_driver.quit)
        cls.addClassCleanup(
            lambda: cls.chrome_driver.get(
                'http://coverage:8000/extra/kill-server/',
            )
        )

    @staticmethod
    def connect_to_web_driver(
            connect_command: Callable[[], WebDriver],
    ) -> WebDriver:  # pragma: no cover
        for attempt_number in range(20):
            sleep(attempt_number * 2)
            try:
                browser_driver = connect_command()
                LOGGER.debug('Success on attempt %s', attempt_number)
                return browser_driver
            except Exception as error:  # pylint: disable=broad-except
                LOGGER.debug(
                    'Received %s error when connecting to chrome driver '
                    'on try %s. %s',
                    type(error),
                    attempt_number,
                    error,
                )
        raise ConnectionError('Could not connect to browser driver')

    def test_normal_flow(self) -> None:
        join_url_1 = self._create_game(self.chrome_driver)
        join_url_2 = self._create_game(self.firefox_driver)
        self._join_game(self.chrome_driver, join_url_2)
        self._join_game(self.firefox_driver, join_url_1)
        self._manipulate_images(
            self.chrome_driver,
            left_transform_matrices=[
                ('matrix(-1.83697e-16, -1, 1, -1.83697e-16, 0, 0)',
                 'matrix(-1.83697e-16, -1, 1, -1.83697e-16, 50, 100)'),
                ('matrix(-1, 1.22465e-16, -1.22465e-16, -1, 100, -50)',
                 'matrix(-1, 1.22465e-16, -1.22465e-16, -1, 150, 50)'),
                ('matrix(6.12323e-17, 1, -1, 6.12323e-17, 50, -150)',
                 'matrix(6.12323e-17, 1, -1, 6.12323e-17, 100, -50)'),
                ('matrix(1, 0, 0, 1, -50, -100)',
                 'matrix(1, 0, 0, 1, 0, 0)'),
            ],
            right_transform_matrices=[
                ('matrix(1, 0, 0, 1, 0, 0)',
                 'matrix(1, 0, 0, 1, 50, 100)'),
                ('matrix(6.12323e-17, 1, -1, 6.12323e-17, -100, 50)',
                 'matrix(6.12323e-17, 1, -1, 6.12323e-17, -50, 150)'),
                ('matrix(-1, 1.22465e-16, -1.22465e-16, -1, -150, -50)',
                 'matrix(-1, 1.22465e-16, -1.22465e-16, -1, -100, 50)'),
                ('matrix(-1.83697e-16, -1, 1, -1.83697e-16, -50, -100)',
                 'matrix(-1.83697e-16, -1, 1, -1.83697e-16, 0, 0)'),
            ],
            coverage_name='chrome',
        )
        self._manipulate_images(
            self.firefox_driver,
            left_transform_matrices=[
                ('matrix(0, -1, 1, 0, 0, 0)',
                 'matrix(0, -1, 1, 0, 50, 100)'),
                ('matrix(-1, 0, 0, -1, 100, -50)',
                 'matrix(-1, 0, 0, -1, 150, 50)'),
                ('matrix(0, 1, -1, 0, 50, -150)',
                 'matrix(0, 1, -1, 0, 100, -50)'),
                ('matrix(1, 0, 0, 1, -50, -100)',
                 'matrix(1, 0, 0, 1, 0, 0)'),
            ],
            right_transform_matrices=[
                ('matrix(1, 0, 0, 1, 0, 0)',
                 'matrix(1, 0, 0, 1, 50, 100)'),
                ('matrix(0, 1, -1, 0, -100, 50)',
                 'matrix(0, 1, -1, 0, -50, 150)'),
                ('matrix(-1, 0, 0, -1, -150, -50)',
                 'matrix(-1, 0, 0, -1, -100, 50)'),
                ('matrix(0, -1, 1, 0, -50, -100)',
                 'matrix(0, -1, 1, 0, 0, 0)'),
            ],
            coverage_name='firefox',
        )

    def _create_game(self, driver: WebDriver) -> str:
        driver.get('http://coverage:8000/games/create/')
        name_elem = driver.find_element_by_id('id_name')
        name_elem.send_keys('Test Admin')
        guess_elem = driver.find_element_by_id('id_total_time_to_guess')
        guess_elem.send_keys('30')
        randomize_elem = driver.find_element_by_id(
            'id_should_randomize_fields'
        )
        randomize_elem.click()
        randomize_elem.click()
        submit_elem = driver.find_element_by_id('id_submit')
        submit_elem.click()
        self.assertEqual('Play', driver.title)
        assert isinstance(driver.current_url, str)
        return driver.current_url

    def _join_game(self, driver: WebDriver, join_url: str) -> None:
        driver.get(join_url)
        self.assertEqual('Join Game', driver.title)
        name_elem = driver.find_element_by_id('id_name')
        name_elem.send_keys('Test Player')
        submit_elem = driver.find_element_by_id('id_submit')
        submit_elem.click()
        self.assertEqual('Play', driver.title)

    def _manipulate_images(
            self,
            driver: WebDriver,
            left_transform_matrices: List[Tuple[str, str]],
            right_transform_matrices: List[Tuple[str, str]],
            coverage_name: str,
    ) -> None:
        image_holder = driver.find_element_by_id('id_image_holder')

        self._test_zoom(driver, image_holder)

        settings_elem = driver.find_element_by_id('id_extra_image_settings')
        expand_settings_elem = driver.find_element_by_id('id_expand_settings')
        self._test_expand_settings(expand_settings_elem, settings_elem)

        self._test_image_transform(
            driver,
            image_holder,
            left_transform_matrices,
            right_transform_matrices,
        )

        image_view_port_elem = driver.find_element_by_id(
            'id_image_view_port',
        )

        self._test_image_filters(
            driver,
            expand_settings_elem,
            image_view_port_elem,
        )

        self._test_thumbnails(driver)
        json_coverage = driver.execute_script(
            'return JSON.stringify(window.__coverage__);',
        )
        with open(
                f'/opt/friendexing/tests/coverage_{coverage_name}.json', 'w'
        ) as json_file:
            json_file.write(json_coverage)

    def _test_zoom(
            self,
            driver: WebDriver,
            image_holder: WebElement,
    ) -> None:
        zoom_in_elem = driver.find_element_by_id('id_zoom_in')
        zoom_in_transforms = (
            'matrix(1.5, 0, 0, 1.5, 0, 0)',
            'matrix(2.25, 0, 0, 2.25, 0, 0)',
            'matrix(3.375, 0, 0, 3.375, 0, 0)',
            'matrix(5.0625, 0, 0, 5.0625, 0, 0)',
            'matrix(7.59375, 0, 0, 7.59375, 0, 0)',
            'matrix(11.3906, 0, 0, 11.3906, 0, 0)',
            'matrix(17.0859, 0, 0, 17.0859, 0, 0)',
            'matrix(25.6289, 0, 0, 25.6289, 0, 0)',
            'matrix(38.4434, 0, 0, 38.4434, 0, 0)',
            'matrix(38.4434, 0, 0, 38.4434, 0, 0)',
        )
        for zoom_in_transform in zoom_in_transforms:
            zoom_in_elem.click()

            transform = image_holder.value_of_css_property('transform')
            self.assertEqual(zoom_in_transform, transform)

        zoom_out_elem = driver.find_element_by_id('id_zoom_out')
        zoom_out_transforms = (
            'matrix(25.6289, 0, 0, 25.6289, 0, 0)',
            'matrix(17.0859, 0, 0, 17.0859, 0, 0)',
            'matrix(11.3906, 0, 0, 11.3906, 0, 0)',
            'matrix(7.59375, 0, 0, 7.59375, 0, 0)',
            'matrix(5.0625, 0, 0, 5.0625, 0, 0)',
            'matrix(3.375, 0, 0, 3.375, 0, 0)',
            'matrix(2.25, 0, 0, 2.25, 0, 0)',
            'matrix(1.5, 0, 0, 1.5, 0, 0)',
            'matrix(1, 0, 0, 1, 0, 0)',
            'matrix(0.666667, 0, 0, 0.666667, 0, 0)',
            'matrix(0.444444, 0, 0, 0.444444, 0, 0)',
            'matrix(0.296296, 0, 0, 0.296296, 0, 0)',
            'matrix(0.197531, 0, 0, 0.197531, 0, 0)',
            'matrix(0.131687, 0, 0, 0.131687, 0, 0)',
            'matrix(0.0877915, 0, 0, 0.0877915, 0, 0)',
            'matrix(0.0877915, 0, 0, 0.0877915, 0, 0)',
        )
        for zoom_out_transform in zoom_out_transforms:
            zoom_out_elem.click()

            transform = image_holder.value_of_css_property('transform')
            self.assertEqual(zoom_out_transform, transform)

        for _ in range(6):
            zoom_in_elem.click()
        transform = image_holder.value_of_css_property('transform')
        self.assertEqual('matrix(1, 0, 0, 1, 0, 0)', transform)

    def _test_expand_settings(
            self,
            expand_settings_elem: WebElement,
            settings_elem: WebElement,
    ) -> None:
        self.assertFalse(settings_elem.is_displayed())
        expand_settings_elem.click()
        self.assertTrue(settings_elem.is_displayed())

    def _test_image_transform(
            self,
            driver: WebDriver,
            image_holder: WebElement,
            left_transform_matrices: List[Tuple[str, str]],
            right_transform_matrices: List[Tuple[str, str]],
    ) -> None:
        main_image_container = driver.find_element_by_id(
            'id_main_image_container',
        )
        rotate_left_elem = driver.find_element_by_id('id_rotate_left')
        for rotation_matrix, translation_matrix in left_transform_matrices:
            rotate_left_elem.click()

            transform = image_holder.value_of_css_property('transform')
            self.assertEqual(rotation_matrix, transform)

            drag_image = ActionChains(driver)
            drag_image.move_to_element_with_offset(
                to_element=main_image_container,
                xoffset=57,
                yoffset=91,
            )
            drag_image.click_and_hold()
            drag_image.move_to_element_with_offset(
                to_element=main_image_container,
                xoffset=107,
                yoffset=191,
            )
            drag_image.release()
            drag_image.perform()

            transform = image_holder.value_of_css_property('transform')
            self.assertEqual(translation_matrix, transform)
        rotate_left_elem.click()

        rotate_right_elem = driver.find_element_by_id('id_rotate_right')
        for rotation_matrix, translation_matrix in right_transform_matrices:
            rotate_right_elem.click()

            transform = image_holder.value_of_css_property('transform')
            self.assertEqual(rotation_matrix, transform)

            drag_image = ActionChains(driver)
            drag_image.move_to_element_with_offset(
                to_element=main_image_container,
                xoffset=57,
                yoffset=91,
            )
            drag_image.click_and_hold()
            drag_image.move_to_element_with_offset(
                to_element=main_image_container,
                xoffset=107,
                yoffset=191,
            )
            drag_image.release()
            drag_image.perform()

            transform = image_holder.value_of_css_property('transform')
            self.assertEqual(translation_matrix, transform)
        rotate_right_elem.click()

    def _test_image_filters(
            self,
            driver: WebDriver,
            expand_settings_elem: WebElement,
            image_view_port_elem: WebElement,
    ) -> None:
        self._test_invert(driver, image_view_port_elem)

        tone_modal = driver.find_element_by_id('id_tone_modal')
        self.assertFalse(tone_modal.is_displayed())

        tone_button = driver.find_element_by_id('id_tone_button')
        tone_button.click()
        self.assertTrue(tone_modal.is_displayed())

        brightness_slider = driver.find_element_by_id('id_brightness_slider')
        contrast_slider = driver.find_element_by_id('id_contrast_slider')
        self._test_apply_modal(
            brightness_slider,
            contrast_slider,
            driver,
            image_view_port_elem,
        )

        tone_button.click()

        self._test_cancel_modal(
            brightness_slider,
            contrast_slider,
            driver,
            image_view_port_elem,
        )

        expand_settings_elem.click()
        wait = WebDriverWait(driver, timeout=5)

        def extra_image_settings_not_displayed(new_driver: WebDriver) -> bool:
            extra_image_settings = new_driver.find_element_by_id(
                'id_extra_image_settings',
            )
            return not extra_image_settings.is_displayed()

        wait.until(extra_image_settings_not_displayed)

    def _test_invert(
            self,
            driver: WebDriver,
            image_view_port_elem: WebElement,
    ) -> None:
        invert_button = driver.find_element_by_id('id_invert_button')
        invert_button.click()

        filter_style = image_view_port_elem.value_of_css_property('filter')

        self.assertEqual('invert(1) contrast(1) brightness(1)', filter_style)

        invert_button.click()

        filter_style = image_view_port_elem.value_of_css_property('filter')

        self.assertEqual('invert(0) contrast(1) brightness(1)', filter_style)

    def _test_apply_modal(
            self,
            brightness_slider: WebElement,
            contrast_slider: WebElement,
            driver: WebDriver,
            image_view_port_elem: WebElement,
    ) -> None:
        move_sliders = ActionChains(driver)
        brightness_slider_size = brightness_slider.size
        contrast_slider_size = contrast_slider.size
        move_sliders.move_to_element_with_offset(
            to_element=brightness_slider,
            xoffset=brightness_slider_size['width'] - 1,
            yoffset=brightness_slider_size['height'] / 2,
        )
        move_sliders.click()

        move_sliders.move_to_element_with_offset(
            to_element=contrast_slider,
            xoffset=contrast_slider_size['width'] - 1,
            yoffset=contrast_slider_size['height'] / 2,
        )
        move_sliders.click()

        move_sliders.perform()
        apply_button = driver.find_element_by_id(
            'id_apply_image_editor_button',
        )
        apply_button.click()

        filter_style = image_view_port_elem.value_of_css_property('filter')

        self.assertEqual('invert(0) contrast(2) brightness(2)', filter_style)

    def _test_cancel_modal(
            self,
            brightness_slider: WebElement,
            contrast_slider: WebElement,
            driver: WebDriver,
            image_view_port_elem: WebElement,
    ) -> None:
        brightness_slider_size = brightness_slider.size
        contrast_slider_size = contrast_slider.size
        move_sliders = ActionChains(driver)
        move_sliders.move_to_element_with_offset(
            to_element=brightness_slider,
            xoffset=1,
            yoffset=brightness_slider_size['height'] / 2,
        )
        move_sliders.click()

        move_sliders.move_to_element_with_offset(
            to_element=contrast_slider,
            xoffset=1,
            yoffset=contrast_slider_size['height'] / 2,
        )
        move_sliders.click()

        move_sliders.perform()

        filter_style = image_view_port_elem.value_of_css_property('filter')

        self.assertEqual('invert(0) contrast(0) brightness(0)', filter_style)

        close_image_editor_button = driver.find_element_by_id(
            'id_close_image_editor_button',
        )
        close_image_editor_button.click()

        filter_style = image_view_port_elem.value_of_css_property('filter')

        self.assertEqual('invert(0) contrast(2) brightness(2)', filter_style)

    def _test_thumbnails(
            self,
            driver: WebDriver,
    ) -> None:
        image_1_elem = driver.find_element_by_id('id_image_1')
        image_2_elem = driver.find_element_by_id('id_image_2')
        self.assertTrue(image_1_elem.is_displayed())
        self.assertFalse(image_2_elem.is_displayed())

        thumbnail_2_elem = driver.find_element_by_id('id_thumbnail_2')
        thumbnail_2_elem.click()
        self.assertFalse(image_1_elem.is_displayed())
        self.assertTrue(image_2_elem.is_displayed())

        thumbnail_2_elem.click()
        self.assertFalse(image_1_elem.is_displayed())
        self.assertTrue(image_2_elem.is_displayed())
