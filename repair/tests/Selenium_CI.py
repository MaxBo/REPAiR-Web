from repair.tests.EditActorTest_orig import EditActorTest
from selenium import webdriver
import unittest

class EditActorTestCI(EditActorTest):
    """
    """
    driver = webdriver.Chrome()


if __name__ == "__main__":
    unittest.main()