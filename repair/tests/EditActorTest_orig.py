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
from repair.tests.selenium_basic import SeleniumBasic

class EditActorTest(SeleniumBasic, unittest.TestCase):

    def setUp(self):
        super().setUp()

    def test_edit_actor(self):
        driver = self.driver
        driver.get("http://localhost:4444/data-entry/")
        driver.find_element_by_xpath("(//button[@type='button'])[4]").click()
        driver.find_element_by_id("data-entry-link").click()
        driver.find_element_by_id("keyflow-select").click()
        Select(driver.find_element_by_id("keyflow-select")).select_by_visible_text("Organic")
        driver.find_element_by_id("keyflow-select").click()
        driver.find_element_by_link_text("Edit Actors").click()
        driver.find_element_by_id("add-actor-button").click()
        driver.find_element_by_xpath("//div[@id='generic-modal']//input").click()
        driver.find_element_by_xpath("//div[@id='generic-modal']//input").clear()
        driver.find_element_by_xpath("//div[@id='generic-modal']//input").send_keys("test123")
        driver.find_element_by_xpath("(//button[@type='button'])[12]").click()
        driver.find_element_by_id("add-administrative-button").click()
        driver.find_element_by_xpath("(//input[@name='name'])[2]").click()
        driver.find_element_by_xpath("(//input[@name='name'])[2]").clear()
        driver.find_element_by_xpath("(//input[@name='name'])[2]").send_keys("test")
        driver.find_element_by_name("city").clear()
        driver.find_element_by_name("city").send_keys("test")
        driver.find_element_by_name("postcode").clear()
        driver.find_element_by_name("postcode").send_keys("test")
        driver.find_element_by_name("address").clear()
        driver.find_element_by_name("address").send_keys("test")
        driver.find_element_by_xpath("//button[@id='add-point']/span").click()
        driver.find_element_by_xpath("//div[@id='edit-location-map']/div/canvas").click()
        driver.find_element_by_xpath("//table[@id='location-area-table']/tbody/tr/td[2]/select").click()
        Select(driver.find_element_by_xpath("//table[@id='location-area-table']/tbody/tr/td[2]/select")).select_by_visible_text("Noord-Holland")
        driver.find_element_by_xpath("//table[@id='location-area-table']/tbody/tr/td[2]/select").click()
        driver.find_element_by_xpath("//table[@id='location-area-table']/tbody/tr[2]/td[2]/select").click()
        Select(driver.find_element_by_xpath("//table[@id='location-area-table']/tbody/tr[2]/td[2]/select")).select_by_visible_text("Amsterdam Metropoolregio")
        driver.find_element_by_xpath("//table[@id='location-area-table']/tbody/tr[2]/td[2]/select").click()
        driver.find_element_by_xpath("//table[@id='location-area-table']/tbody/tr[3]/td[2]/select").click()
        Select(driver.find_element_by_xpath("//table[@id='location-area-table']/tbody/tr[3]/td[2]/select")).select_by_visible_text("Heemskerk")
        driver.find_element_by_xpath("//table[@id='location-area-table']/tbody/tr[3]/td[2]/select").click()
        driver.find_element_by_xpath("//table[@id='location-area-table']/tbody/tr[4]/td[2]/select").click()
        Select(driver.find_element_by_xpath("//table[@id='location-area-table']/tbody/tr[4]/td[2]/select")).select_by_visible_text("Wijk 01 Heemskerk-Dorp")
        driver.find_element_by_xpath("//table[@id='location-area-table']/tbody/tr[4]/td[2]/select").click()
        driver.find_element_by_id("confirm-location").click()
        driver.find_element_by_id("upload-actor-button").click()
        #driver.find_element_by_xpath("//input[@type='search']").click()
        #driver.find_element_by_xpath("//input[@type='search']").clear()
        #driver.find_element_by_xpath("//input[@type='search']").send_keys("test123")

    def is_element_present(self, how, what):
        try: self.driver.find_element(by=how, value=what)
        except NoSuchElementException as e: return False
        return True

    def is_alert_present(self):
        try: self.driver.switch_to_alert()
        except NoAlertPresentException as e: return False
        return True

    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally: self.accept_next_alert = True

    def tearDown(self):
        super().tearDown()
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)




if __name__ == "__main__":
    unittest.main()
