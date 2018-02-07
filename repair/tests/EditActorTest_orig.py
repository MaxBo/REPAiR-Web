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
        # login
        driver.find_element_by_css_selector("#login-link > div.dropdown > button.dropdown-button").click()
        driver.find_element_by_id("data-entry-lin"
                                  "k").click()
        driver.find_element_by_link_text("Edit Actors").click()
        driver.find_element_by_id("keyflow-select").click()
        Select(driver.find_element_by_id("keyflow-select")).select_by_visible_text("Organic")
        driver.find_element_by_id("keyflow-select").click()
        driver.find_element_by_id("included-filter-select").click()
        Select(driver.find_element_by_id("included-filter-select")).select_by_visible_text("show included only")
        driver.find_element_by_id("included-filter-select").click()
        driver.find_element_by_id("included-filter-select").click()
        Select(driver.find_element_by_id("included-filter-select")).select_by_visible_text("show all")
        driver.find_element_by_id("included-filter-select").click()
        driver.find_element_by_css_selector("th.tablesorter-header.tablesorter-headerUnSorted").click()
        driver.find_element_by_css_selector("th.tablesorter-header.tablesorter-headerAsc").click()
        driver.find_element_by_css_selector("th.tablesorter-header.tablesorter-headerUnSorted").click()
        driver.find_element_by_css_selector("th.tablesorter-header.tablesorter-headerAsc").click()
        driver.find_element_by_css_selector("input.tablesorter-filter").click()
        driver.find_element_by_css_selector("input.tablesorter-filter").clear()
        driver.find_element_by_css_selector("input.tablesorter-filter").send_keys("3D")
        driver.find_element_by_css_selector("input.tablesorter-filter").send_keys(Keys.ENTER)
        driver.find_element_by_xpath("(//input[@type='search'])[2]").click()
        driver.find_element_by_css_selector("input.tablesorter-filter").clear()
        driver.find_element_by_css_selector("input.tablesorter-filter").send_keys("")
        driver.find_element_by_xpath("(//input[@type='search'])[2]").click()
        driver.find_element_by_xpath("(//input[@type='search'])[2]").clear()
        driver.find_element_by_xpath("(//input[@type='search'])[2]").send_keys("bar")
        driver.find_element_by_xpath("(//input[@type='search'])[2]").send_keys(Keys.ENTER)
        driver.find_element_by_css_selector("input.tablesorter-filter").click()
        driver.find_element_by_css_selector("input.tablesorter-filter").clear()
        driver.find_element_by_css_selector("input.tablesorter-filter").send_keys("bar")
        driver.find_element_by_css_selector("input.tablesorter-filter").send_keys(Keys.ENTER)
        driver.find_element_by_css_selector("input.tablesorter-filter").click()
        driver.find_element_by_css_selector("input.tablesorter-filter").clear()
        driver.find_element_by_css_selector("input.tablesorter-filter").send_keys("dictum")
        driver.find_element_by_css_selector("input.tablesorter-filter").send_keys(Keys.ENTER)
        driver.find_element_by_xpath("(//input[@type='search'])[2]").click()
        driver.find_element_by_css_selector("input.tablesorter-filter").clear()
        driver.find_element_by_css_selector("input.tablesorter-filter").send_keys("")
        driver.find_element_by_xpath("(//input[@type='search'])[2]").click()
        driver.find_element_by_xpath("(//input[@type='search'])[2]").clear()
        driver.find_element_by_xpath("(//input[@type='search'])[2]").send_keys("supply")
        driver.find_element_by_xpath("(//input[@type='search'])[2]").send_keys(Keys.ENTER)
        driver.find_element_by_css_selector("input.tablesorter-filter").click()
        driver.find_element_by_css_selector("img.next").click()
        driver.find_element_by_css_selector("img.next").click()
        driver.find_element_by_id("included-filter-select").click()
        driver.find_element_by_css_selector("input.tablesorter-filter").clear()
        driver.find_element_by_css_selector("input.tablesorter-filter").send_keys("farm")
        driver.find_element_by_css_selector("#add-actor-button > span.glyphicon.glyphicon-plus").click()
        driver.find_element_by_name("name").clear()
        driver.find_element_by_name("name").send_keys("Glass bottle maker_test")
        driver.find_element_by_name("activity").click()
        driver.find_element_by_name("name").click()
        driver.find_element_by_name("name").clear()
        driver.find_element_by_name("name").send_keys("vegetable maker_test")
        driver.find_element_by_name("activity").click()
        driver.find_element_by_name("activity").click()
        driver.find_element_by_name("website").clear()
        driver.find_element_by_name("website").send_keys("www.vegemaker.com")
        driver.find_element_by_name("year").click()
        driver.find_element_by_name("year").clear()
        driver.find_element_by_name("year").send_keys("2015")
        driver.find_element_by_name("turnover").clear()
        driver.find_element_by_name("turnover").send_keys("1")
        driver.find_element_by_name("turnover").click()
        driver.find_element_by_name("turnover").click()
        driver.find_element_by_name("turnover").clear()
        driver.find_element_by_name("turnover").send_keys("2")
        driver.find_element_by_name("turnover").clear()
        driver.find_element_by_name("turnover").send_keys("14000")
        driver.find_element_by_name("employees").click()
        driver.find_element_by_name("employees").clear()
        driver.find_element_by_name("employees").send_keys("400")
        driver.find_element_by_name("BvDid").clear()
        driver.find_element_by_name("BvDid").send_keys("NL123")
        driver.find_element_by_name("BvDii").clear()
        driver.find_element_by_name("BvDii").send_keys("1234")
        driver.find_element_by_name("consCode").click()
        driver.find_element_by_name("consCode").clear()
        driver.find_element_by_name("consCode").send_keys("4444")
        driver.find_element_by_id("add-administrative-button").click()
        driver.find_element_by_css_selector("#location-modal-content > input[name=\"name\"]").click()
        driver.find_element_by_css_selector("#location-modal-content > input[name=\"name\"]").clear()
        driver.find_element_by_css_selector("#location-modal-content > input[name=\"name\"]").send_keys("Headquarter")
        driver.find_element_by_name("city").click()
        driver.find_element_by_name("city").clear()
        driver.find_element_by_name("city").send_keys("Den Haag")
        driver.find_element_by_name("postcode").click()
        driver.find_element_by_name("postcode").clear()
        driver.find_element_by_name("postcode").send_keys("1122 jj")
        driver.find_element_by_css_selector("#add-point > span.glyphicon.glyphicon-plus").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > canvas.ol-unselectable").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > canvas.ol-unselectable").click()
        driver.find_element_by_id("confirm-location").click()
        driver.find_element_by_id("add-operational-button").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > canvas.ol-unselectable").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > canvas.ol-unselectable").click()
        # ERROR: Caught exception [ERROR: Unsupported command [doubleClick | css=#edit-location-map > div.ol-viewport > canvas.ol-unselectable | ]]
        driver.find_element_by_css_selector("#location-modal-content > input[name=\"name\"]").click()
        driver.find_element_by_css_selector("#location-modal-content > input[name=\"name\"]").clear()
        driver.find_element_by_css_selector("#location-modal-content > input[name=\"name\"]").send_keys("Branch 1")
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > div.ol-overlaycontainer-stopevent > div.ol-zoom.ol-unselectable.ol-control > button.ol-zoom-in").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > div.ol-overlaycontainer-stopevent > div.ol-zoom.ol-unselectable.ol-control > button.ol-zoom-in").click()
        # ERROR: Caught exception [ERROR: Unsupported command [doubleClick | css=#edit-location-map > div.ol-viewport > div.ol-overlaycontainer-stopevent > div.ol-zoom.ol-unselectable.ol-control > button.ol-zoom-in | ]]
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > div.ol-overlaycontainer-stopevent > div.ol-zoom.ol-unselectable.ol-control > button.ol-zoom-in").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > canvas.ol-unselectable").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > canvas.ol-unselectable").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > canvas.ol-unselectable").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > div.ol-overlaycontainer-stopevent > div.ol-zoom.ol-unselectable.ol-control > button.ol-zoom-out").click()
        driver.find_element_by_name("city").click()
        driver.find_element_by_name("city").clear()
        driver.find_element_by_name("city").send_keys("Hoorfdorp")
        driver.find_element_by_name("postcode").click()
        driver.find_element_by_name("postcode").clear()
        driver.find_element_by_name("postcode").send_keys("2211 oo")
        driver.find_element_by_css_selector("#add-point > span.glyphicon.glyphicon-plus").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > canvas.ol-unselectable").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > canvas.ol-unselectable").click()
        driver.find_element_by_id("confirm-location").click()
        driver.find_element_by_id("add-operational-button").click()
        driver.find_element_by_css_selector("#location-modal-content > input[name=\"name\"]").click()
        driver.find_element_by_css_selector("#location-modal-content > input[name=\"name\"]").clear()
        driver.find_element_by_css_selector("#location-modal-content > input[name=\"name\"]").send_keys("branch 2")
        driver.find_element_by_name("city").click()
        driver.find_element_by_name("city").clear()
        driver.find_element_by_name("city").send_keys("nieuw-vennep")
        driver.find_element_by_css_selector("#add-point > span.glyphicon.glyphicon-plus").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > canvas.ol-unselectable").click()
        driver.find_element_by_id("confirm-location").click()
        driver.find_element_by_id("upload-actor-button").click()
        driver.find_element_by_id("included-check").click()
        #driver.find_element_by_name("reason").click()
        time.sleep(5)
        driver.find_element_by_id("upload-actor-button").click()
        driver.find_element_by_css_selector("input.tablesorter-filter").click()
        driver.find_element_by_id("pagesize").click()
        driver.find_element_by_css_selector("input.pagedisplay").click()
        driver.find_element_by_id("goto-first-page").click()
        # added this:
        driver.find_element_by_xpath("(//input[@type='search'])[2]").clear()
        driver.find_element_by_css_selector("input.tablesorter-filter").clear()
        #
        driver.find_element_by_xpath("//table[@id='actors-table']/tbody/tr/td[1]").click()
        driver.find_element_by_id("included-check").click()
        driver.find_element_by_xpath("(//input[@name='reason'])[3]").click()
        driver.find_element_by_id("upload-actor-button").click()
        driver.find_element_by_xpath("//table[@id='actors-table']/tbody/tr[2]/td[2]").click()
        driver.find_element_by_id("included-filter-select").click()
        Select(driver.find_element_by_id("included-filter-select")).select_by_visible_text("show included only")
        driver.find_element_by_id("included-filter-select").click()
        driver.find_element_by_id("included-filter-select").click()
        Select(driver.find_element_by_id("included-filter-select")).select_by_visible_text("show all")
        driver.find_element_by_id("included-filter-select").click()
        driver.find_element_by_xpath("//table[@id='actors-table']/tbody/tr[6]/td").click()
        driver.find_element_by_css_selector("tr.dsbld > td").click()
        driver.find_element_by_id("remove-actor-button").click()
        driver.find_element_by_id("confirm-button").click()
        driver.find_element_by_xpath("//table[@id='actors-table']/tbody/tr[6]/td[2]").click()
        driver.find_element_by_id("included-check").click()
        driver.find_element_by_id("included-check").click()
        driver.find_element_by_id("included-check").click()
        driver.find_element_by_name("name").click()
        driver.find_element_by_name("name").clear()
        driver.find_element_by_name("name").send_keys("vegetable maker-test")
        driver.find_element_by_name("activity").click()
        Select(driver.find_element_by_name("activity")).select_by_visible_text("Event catering activities")
        driver.find_element_by_name("activity").click()
        driver.find_element_by_name("website").click()
        driver.find_element_by_name("turnover").clear()
        driver.find_element_by_name("turnover").send_keys("14001")
        driver.find_element_by_name("turnover").click()
        driver.find_element_by_name("employees").clear()
        driver.find_element_by_name("employees").send_keys("399")
        driver.find_element_by_name("employees").click()
        driver.find_element_by_css_selector("span.glyphicon.glyphicon-pencil").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > canvas.ol-unselectable").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > canvas.ol-unselectable").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > canvas.ol-unselectable").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > canvas.ol-unselectable").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > canvas.ol-unselectable").click()
        # ERROR: Caught exception [ERROR: Unsupported command [doubleClick | css=#edit-location-map > div.ol-viewport > canvas.ol-unselectable | ]]
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > canvas.ol-unselectable").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > canvas.ol-unselectable").click()
        # ERROR: Caught exception [ERROR: Unsupported command [doubleClick | css=#edit-location-map > div.ol-viewport > canvas.ol-unselectable | ]]
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > canvas.ol-unselectable").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > canvas.ol-unselectable").click()
        # ERROR: Caught exception [ERROR: Unsupported command [doubleClick | css=#edit-location-map > div.ol-viewport > canvas.ol-unselectable | ]]
        driver.find_element_by_css_selector("#remove-point > span.glyphicon.glyphicon-minus").click()
        driver.find_element_by_css_selector("#add-point > span.glyphicon.glyphicon-plus").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > div.ol-overlaycontainer-stopevent > div.ol-zoom.ol-unselectable.ol-control > button.ol-zoom-in").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > div.ol-overlaycontainer-stopevent > div.ol-zoom.ol-unselectable.ol-control > button.ol-zoom-out").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > div.ol-overlaycontainer-stopevent > div.ol-zoom.ol-unselectable.ol-control > button.ol-zoom-out").click()
        # ERROR: Caught exception [ERROR: Unsupported command [doubleClick | css=#edit-location-map > div.ol-viewport > div.ol-overlaycontainer-stopevent > div.ol-zoom.ol-unselectable.ol-control > button.ol-zoom-out | ]]
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > div.ol-overlaycontainer-stopevent > div.ol-zoom.ol-unselectable.ol-control > button.ol-zoom-out").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > div.ol-overlaycontainer-stopevent > div.ol-zoom.ol-unselectable.ol-control > button.ol-zoom-out").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > div.ol-overlaycontainer-stopevent > div.ol-zoom.ol-unselectable.ol-control > button.ol-zoom-out").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > div.ol-overlaycontainer-stopevent > div.ol-zoom.ol-unselectable.ol-control > button.ol-zoom-in").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > div.ol-overlaycontainer-stopevent > div.ol-zoom.ol-unselectable.ol-control > button.ol-zoom-in").click()
        # ERROR: Caught exception [ERROR: Unsupported command [doubleClick | css=#edit-location-map > div.ol-viewport > div.ol-overlaycontainer-stopevent > div.ol-zoom.ol-unselectable.ol-control > button.ol-zoom-in | ]]
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > div.ol-overlaycontainer-stopevent > div.ol-zoom.ol-unselectable.ol-control > button.ol-zoom-in").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > div.ol-overlaycontainer-stopevent > div.ol-zoom.ol-unselectable.ol-control > button.ol-zoom-in").click()
        # ERROR: Caught exception [ERROR: Unsupported command [doubleClick | css=#edit-location-map > div.ol-viewport > div.ol-overlaycontainer-stopevent > div.ol-zoom.ol-unselectable.ol-control > button.ol-zoom-in | ]]
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > canvas.ol-unselectable").click()
        driver.find_element_by_css_selector("#edit-location-map > div.ol-viewport > canvas.ol-unselectable").click()
        driver.find_element_by_id("confirm-location").click()
        driver.find_element_by_id("upload-actor-button").click()
        driver.find_element_by_id("refresh-actorsview-btn").click()
        driver.find_element_by_xpath("//table[@id='actors-table']/tbody/tr[3]/td").click()
        driver.find_element_by_id("refresh-actorsview-btn").click()
        driver.find_element_by_css_selector("img.next").click()
        driver.find_element_by_id("pagesize").click()
        driver.find_element_by_id("pagesize").click()
        #driver.find_element_by_css_selector("tr.selected > td").click()
        #driver.find_element_by_xpath("(//input[@type='checkbox'])[4]").click()
        #driver.find_element_by_id("upload-actor-button").click()

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
