# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
import unittest, time, re
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.command import Command
import time
import os


class CustomWebElement(WebElement):

    def click(self, x_off=0, y_off=0):
        """Clicks the element."""
        # write click information into log file:
        file_dir = os.path.dirname(__file__)
        artifacts_dir = os.path.join(file_dir, 'artifacts')
        fn = os.path.join(artifacts_dir, 'click_log.txt')
        log_file = open(fn, "a")
        log_file.write(
            "\ntag_name: {}; text: {}; location: {}\n".format(self.tag_name,
                                                              self.text,
                                                              self.location))
        log_file.close()
        # save screenshot:
        self.driver.get_screenshot_as_file(
            os.path.join(artifacts_dir,
                         'screenshots/click{}.png'.format(time.time())))
        # do clicking:
        try:
            self._execute(Command.CLICK_ELEMENT)
        except Exception:
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            self.driver.execute_script("window.scrollTo(0, 0);")
            hover = ActionChains(self.driver)
            x_pos = self.location['x']
            if x_pos < 0:
                x_off -= (x_pos - 5)
            hover.move_to_element_with_offset(self, x_off, y_off
                                              ).click().perform()
            if x_off > 0:
                hover.move_to_element_with_offset(self, 500, 0).perform()

class SeleniumBasic(object):

    local_driver = r'F:\Downloads\chromedriver.exe'
    driver = webdriver.Chrome()
    WebElement.click = CustomWebElement.click
    WebElement.driver = driver

    def setUp(self):
        file_dir = os.path.dirname(__file__)
        os.mkdir(os.path.join(file_dir, 'artifacts'))
        artifacts_dir = os.path.join(file_dir, 'artifacts')
        os.mkdir(os.path.join(artifacts_dir, 'screenshots'))
        fn = os.path.join(artifacts_dir, 'click_log.txt')
        log_file = open(fn, "a")
        log_file.write("SetUp\n")
        log_file.close()

        self.driver.implicitly_wait(20)
        self.verificationErrors = []
        self.accept_next_alert = True
        driver = self.driver
        driver.get("localhost:4444")
        #driver.maximize_window()
        driver.set_window_size(1936, 1056)
        driver.find_element_by_css_selector("span.caret").click()
        driver.find_element_by_css_selector("button.dropdown-button").click()
        driver.find_element_by_link_text("SandboxCity").click()
        driver.find_element_by_link_text("Login").click()
        driver.find_element_by_id("id_username").click()
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("stefaan")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("84568456a")
        driver.find_element_by_id("submit-id-submit").click()

    def tearDown(self):
        file_dir = os.path.dirname(__file__)
        print("save at {}".format(os.path.join(file_dir,
                                               'artifacts',
                                               'error.png')))
        self.driver.get_screenshot_as_file(os.path.join(file_dir,
                                                        'artifacts',
                                                        'error.png'))
