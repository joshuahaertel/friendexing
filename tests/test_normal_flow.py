import logging
import os
from functools import partial
from time import sleep
from typing import Callable, Iterable
from unittest import TestCase

from selenium import webdriver
from selenium.webdriver import DesiredCapabilities, ActionChains
from selenium.webdriver.remote.webdriver import WebDriver
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
            rotation_matrices=(
                'matrix(-1.83697e-16, -1, 1, -1.83697e-16, 0, 0)',
                'matrix(-1, 1.22465e-16, -1.22465e-16, -1, 0, 0)',
                'matrix(6.12323e-17, 1, -1, 6.12323e-17, 0, 0)',
                'matrix(1, 0, 0, 1, 0, 0)',
            )
        )
        self._manipulate_images(
            self.firefox_driver,
            rotation_matrices=(
                'matrix(0, -1, 1, 0, 0, 0)',
                'matrix(-1, 0, 0, -1, 0, 0)',
                'matrix(0, 1, -1, 0, 0, 0)',
                'matrix(1, 0, 0, 1, 0, 0)',
            )
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
            rotation_matrices: Iterable[str],
    ):
        image_holder = driver.find_element_by_id('id_image_holder')

        zoom_in_elem = driver.find_element_by_id('id_zoom_in')
        zoom_in_elem.click()

        transform = image_holder.value_of_css_property('transform')
        self.assertEqual('matrix(1.5, 0, 0, 1.5, 0, 0)', transform)

        zoom_out_elem = driver.find_element_by_id('id_zoom_out')
        zoom_out_elem.click()

        transform = image_holder.value_of_css_property('transform')
        self.assertEqual('matrix(1, 0, 0, 1, 0, 0)', transform)

        settings_elem = driver.find_element_by_id('id_extra_image_settings')
        self.assertFalse(settings_elem.is_displayed())

        expand_settings_elem = driver.find_element_by_id('id_expand_settings')
        expand_settings_elem.click()
        self.assertTrue(settings_elem.is_displayed())

        rotate_left_elem = driver.find_element_by_id('id_rotate_left')
        for rotation_matrix in rotation_matrices:
            rotate_left_elem.click()

            transform = image_holder.value_of_css_property('transform')
            self.assertEqual(rotation_matrix, transform)
        rotate_left_elem.click()

        rotate_right_elem = driver.find_element_by_id('id_rotate_right')
        for rotation_matrix in reversed(rotation_matrices):
            rotate_right_elem.click()

            transform = image_holder.value_of_css_property('transform')
            self.assertEqual(rotation_matrix, transform)
        rotate_right_elem.click()

        image_view_port_element = driver.find_element_by_id(
            'id_image_view_port',
        )

        invert_button = driver.find_element_by_id('id_invert_button')
        invert_button.click()

        filter_style = image_view_port_element.value_of_css_property('filter')
        self.assertEqual('invert(1) contrast(1) brightness(1)', filter_style)

        invert_button.click()

        filter_style = image_view_port_element.value_of_css_property('filter')
        self.assertEqual('invert(0) contrast(1) brightness(1)', filter_style)

        tone_modal = driver.find_element_by_id('id_tone_modal')
        self.assertFalse(tone_modal.is_displayed())

        tone_button = driver.find_element_by_id('id_tone_button')
        tone_button.click()
        self.assertTrue(tone_modal.is_displayed())

        brightness_slider = driver.find_element_by_id('id_brightness_slider')
        brightness_slider_size = brightness_slider.size
        move_sliders = ActionChains(driver)
        move_sliders.move_to_element_with_offset(
            to_element=brightness_slider,
            xoffset=brightness_slider_size['width'] - 1,
            yoffset=brightness_slider_size['height'] / 2,
        )
        move_sliders.click()

        contrast_slider = driver.find_element_by_id('id_contrast_slider')
        contrast_slider_size = contrast_slider.size
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

        filter_style = image_view_port_element.value_of_css_property('filter')
        self.assertEqual('invert(0) contrast(2) brightness(2)', filter_style)

        tone_button.click()

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

        filter_style = image_view_port_element.value_of_css_property('filter')
        self.assertEqual('invert(0) contrast(0) brightness(0)', filter_style)

        close_image_editor_button = driver.find_element_by_id(
            'id_close_image_editor_button',
        )
        close_image_editor_button.click()

        filter_style = image_view_port_element.value_of_css_property('filter')
        self.assertEqual('invert(0) contrast(2) brightness(2)', filter_style)

        expand_settings_elem.click()
        wait = WebDriverWait(driver, timeout=5)

        def extra_image_settings_not_displayed(new_driver: WebDriver):
            extra_image_settings = new_driver.find_element_by_id(
                'id_extra_image_settings',
            )
            return not extra_image_settings.is_displayed()

        wait.until(extra_image_settings_not_displayed)

        main_image_container = driver.find_element_by_id(
            'id_main_image_container',
        )
        drag_image = ActionChains(driver)
        drag_image.move_to_element_with_offset(
            to_element=main_image_container,
            xoffset=28,
            yoffset=90,
        )
        drag_image.click_and_hold()
        drag_image.move_to_element_with_offset(
            to_element=main_image_container,
            xoffset=128,
            yoffset=190,
        )
        drag_image.release()
        drag_image.perform()

        transform = image_holder.value_of_css_property('transform')
        self.assertEqual('matrix(1, 0, 0, 1, 100, 100)', transform)

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
