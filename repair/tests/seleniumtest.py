# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
import unittest, time, re

class Google3(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(30)
        self.base_url = "https://www.katalon.com/"
        self.verificationErrors = []
        self.accept_next_alert = True

    def test_google3(self):
        driver = self.driver
        driver.get("https://www.google.de/search?safe=off&hl=de&source=hp&ei=32dXWtvRKYKSsgG3wJXACg&q=how+much+is+the+fish&oq=how+much+is+the+fish&gs_l=psy-ab.1.0.0l10.12844.16432.0.18114.23.21.0.0.0.0.162.2159.5j15.21.0....0...1.1.64.psy-ab..2.20.2157.0..0i131k1.142.2jkp68NLt3E")
        time.sleep(5)
        driver.find_element_by_link_text("How Much Is the Fish? - Wikipedia").click()
        time.sleep(5)
        driver.find_element_by_xpath("//div[@id='toc']/ul/li/a/span[2]").click()
        time.sleep(5)
        driver.find_element_by_link_text(u"Ö3 Austria Top 40").click()

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
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
