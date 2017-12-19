from django.test import TestCase
from django.core.validators import ValidationError
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from repair.tests.test import BasicModelTest

from repair.apps.studyarea.factories import (CaseStudyFactory,
                                             StakeholderCategoryFactory,
                                             StakeholderFactory,
                                             )



class UniqueStakeholderNames(TestCase):


    def test03_unique_stakeholdercategory(self):
        """Test the unique stakeholder name"""
        city1 = CaseStudyFactory(name='City1')
        city2 = CaseStudyFactory(name='City1')
        stakeholdercat1 = StakeholderCategoryFactory(
            casestudy=city1, name='Cat1')
        stakeholdercat2 = StakeholderCategoryFactory(
            casestudy=city1, name='Cat2')
        stakeholdercat3 = StakeholderCategoryFactory(
            casestudy=city2, name='Cat1')

        with self.assertRaisesMessage(
            ValidationError,
            'StakeholderCategory Cat1 already exists in casestudy City1',
            ) as err:
            stakeholdercat3 = StakeholderCategoryFactory(
                casestudy=city2, name='Cat1')
        print(err.exception.messages)


class StakeholdercategoryInCasestudyTest(BasicModelTest, APITestCase):

    casestudy = 17
    stakeholdercategory = 48
    #solutioncategory = 21
    #solution = 36
    #solutionquantity = 28
    userincasestudy = 67
    user = 99
    #unit = 75
    #solutionratiooneunit = 84
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "stakeholdercategory"
        cls.url_pks = dict(casestudy_pk=cls.casestudy)
        cls.url_pk = dict(pk=cls.stakeholdercategory)
        cls.post_data = dict(name='posttestname')
        cls.put_data = cls.post_data
        cls.patch_data = dict(name="test name")

    def setUp(self):
        self.obj = StakeholderCategoryFactory(id=self.stakeholdercategory,
                                              casestudy=self.uic.casestudy,
                                              )

    def test_post(self):
        """
        MAX
        """
        pass


class StakeholdercategoryInCasestudyTest(BasicModelTest, APITestCase):

    casestudy = 17
    stakeholdercategory = 48
    stakeholder = 21
    #solution = 36
    #solutionquantity = 28
    userincasestudy = 67
    user = 99
    #unit = 75
    #solutionratiooneunit = 84
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stakeholdercategory_url = cls.baseurl + \
            reverse('stakeholdercategory-detail',
                    kwargs=dict(casestudy_pk=cls.casestudy,
                                pk=cls.stakeholdercategory))
        cls.url_key = "stakeholder"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           stakeholdercategory_pk=cls.stakeholdercategory)
        cls.url_pk = dict(pk=cls.stakeholder)
        cls.post_data = dict(name='posttestname',
                             stakeholder_category=cls.stakeholdercategory_url)
        cls.put_data = cls.post_data
        cls.patch_data = dict(name="test name")

    def setUp(self):
        self.obj = StakeholderFactory(id=self.stakeholder,
                                      stakeholder_category__id=\
                                      self.stakeholdercategory,
                                      stakeholder_category__casestudy=\
                                      self.uic.casestudy,
                                      )



