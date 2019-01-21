# -*- coding: UTF-8 -*-
import unittest
from django.test import TestCase
from django.urls import reverse
from test_plus import APITestCase
from rest_framework import status


unittest.skip('Test not implemented yet')
class ProtectionTest(TestCase):

    def test_protection_of_referenced_objects(self):
        """
        Test if the deletion of an object fails, if there are related objects
        using on_delete=PROTECT_CASCADE and we use use_protection=True
        """

    def test_without_protection_of_referenced_objects(self):
        """
        Test if the deletion of an object works, if there are related objects
        using on_delete=PROTECT_CASCADE and we use use_protection=False
        """
