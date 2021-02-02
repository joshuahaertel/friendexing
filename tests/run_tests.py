import sys
from time import sleep

from selenium import webdriver
from selenium.webdriver import DesiredCapabilities

for attempt_number in range(20):
    sleep(attempt_number * 2)
    try:
        browser = webdriver.Remote(
            command_executor='http://chromium:4444/wd/hub',
            desired_capabilities=DesiredCapabilities.CHROME,
        )
        print(f'Success on attempt {attempt_number}')
        break
    except Exception as error:
        print(attempt_number, type(error), error)
else:
    sys.exit()

browser.get('http://web:8000/games/create/')

name_elem = browser.find_element_by_id('id_name')
name_elem.send_keys('Test Admin')

guess_elem = browser.find_element_by_id('id_total_time_to_guess')
guess_elem.send_keys('30')

randomize_elem = browser.find_element_by_id('id_should_randomize_fields')
randomize_elem.click()

submit_elem = browser.find_element_by_id('id_submit')
submit_elem.click()

print(browser.title)

browser.quit()
