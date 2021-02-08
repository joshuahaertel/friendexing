import logging
import os
from functools import partial
from time import sleep
from typing import Callable
from unittest import TestCase

from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.remote.webdriver import WebDriver

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
