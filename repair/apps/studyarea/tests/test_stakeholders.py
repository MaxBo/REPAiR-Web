from django.test import TestCase
from django.core.validators import ValidationError
from django.urls import reverse

from test_plus import APITestCase
from repair.tests.test import BasicModelPermissionTest

from repair.apps.studyarea.factories import (CaseStudyFactory,
                                             StakeholderCategoryFactory,
                                             StakeholderFactory,
                                             )


class UniqueStakeholderNames(TestCase):
    """Test that the names are unique within a casestudy"""

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

        stakeholder_categories = city1.stakeholder_categories
        self.assertSetEqual(stakeholder_categories, {stakeholdercat1,
                                                     stakeholdercat2})


class StakeholdercategoryInCasestudyTest(BasicModelPermissionTest,
                                         APITestCase):

    casestudy = 17
    stakeholdercategory = 48
    userincasestudy = 67
    user = 99

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
        super().setUp()
        self.obj = StakeholderCategoryFactory(id=self.stakeholdercategory,
                                              casestudy=self.uic.casestudy,
                                              )

    def tearDown(self):
        del self.obj
        super().tearDown()


class StakeholderInCasestudyTest(BasicModelPermissionTest, APITestCase):

    casestudy = 17
    stakeholdercategory = 48
    userincasestudy = 67
    user = 99

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
        cls.url_pk = dict(pk=cls.obj.id)
        cls.post_data = dict(name='posttestname',
                             stakeholder_category=cls.stakeholdercategory_url)
        cls.put_data = cls.post_data
        cls.patch_data = dict(name="test name")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.obj = StakeholderFactory(
            stakeholder_category__id=cls.stakeholdercategory,
            stakeholder_category__casestudy=cls.uic.casestudy,
            )
