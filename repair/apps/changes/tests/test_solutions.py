
from django.urls import reverse
from test_plus import APITestCase
from repair.tests.test import BasicModelTest

from repair.apps.changes.factories import (
    SolutionCategoryFactory,
    SolutionFactory,
    SolutionQuantityFactory,
    SolutionRatioOneUnitFactory,
)


class SolutioncategoryInCasestudyTest(BasicModelTest, APITestCase):

    casestudy = 17
    solutioncategory = 21
    user = 99
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "solutioncategory"
        cls.url_pks = dict(casestudy_pk=cls.casestudy)
        cls.url_pk = dict(pk=cls.solutioncategory)
        cls.post_data = dict(
            name='posttestname',
            user=cls.baseurl + reverse(
                'userincasestudy-detail',
                kwargs=dict(pk=cls.uic.id, casestudy_pk=cls.casestudy)))
        cls.put_data = cls.post_data


    def setUp(self):
        super().setUp()
        self.obj = SolutionCategoryFactory(id=self.solutioncategory,
                                           user=self.uic,
                                           )


class SolutionInSolutioncategoryInCasestudyTest(BasicModelTest, APITestCase):

    casestudy = 17
    solutioncategory = 21
    solution = 36
    userincasestudy = 67
    user = 99
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.solutioncategory_url = cls.baseurl + \
            reverse('solutioncategory-detail',
                    kwargs=dict(pk=cls.solutioncategory,
                                casestudy_pk=cls.casestudy))
        cls.url_key = "solution"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           solutioncategory_pk=cls.solutioncategory)
        cls.url_pk = dict(pk=cls.solution)
        cls.post_data = dict(name='posttestname',
                             user=cls.baseurl + \
                             reverse('userincasestudy-detail',
                                     kwargs=dict(pk=cls.uic.id,
                                                 casestudy_pk=cls.casestudy)),
                             description="This is a description",
                             one_unit_equals='20',
                             solution_category=cls.solutioncategory_url,
                             )
        cls.put_data = cls.post_data
        cls.patch_data = dict(name="test name")

    def setUp(self):
        super().setUp()
        self.obj = SolutionFactory(
            id=self.solution,
            solution_category__id=self.solutioncategory,
            solution_category__user=self.uic,
            user=self.uic,
        )


class SolutionquantityInSolutionInSolutioncategoryInCasestudyTest(
    BasicModelTest, APITestCase):

    casestudy = 17
    solutioncategory = 21
    solution = 36
    solutionquantity = 28
    userincasestudy = 67
    user = 99
    unit = 75
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.unit_url = cls.baseurl + reverse('unit-detail',
                                             kwargs=dict(pk=cls.unit))

        cls.url_key = "solutionquantity"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           solutioncategory_pk=cls.solutioncategory,
                           solution_pk=cls.solution)
        cls.url_pk = dict(pk=cls.solutionquantity)
        cls.post_data = dict(name='posttestname',
                             unit=cls.unit_url,
                             )
        cls.put_data = cls.post_data
        cls.patch_data = dict(name="test name")

    def setUp(self):
        super().setUp()
        self.obj = SolutionQuantityFactory(
            id=self.solutionquantity,
            solution__id=self.solution,
            unit__id=self.unit,
            solution__solution_category__id=self.solutioncategory,
            solution__solution_category__user=self.uic,
            solution__user=self.uic,
            )


class SolutionratiooneunitInSolutionInSolutioncategoryInCasestudyTest(BasicModelTest, APITestCase):

    casestudy = 17
    solutioncategory = 21
    solution = 36
    solutionquantity = 28
    userincasestudy = 67
    user = 99
    unit = 75
    solutionratiooneunit = 84
    do_not_check = ['value']
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.unit_url = cls.baseurl + reverse('unit-detail',
                                             kwargs=dict(pk=cls.unit))
        cls.url_key = "solutionratiooneunit"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           solutioncategory_pk=cls.solutioncategory,
                           solution_pk=cls.solution)
        cls.url_pk = dict(pk=cls.solutionratiooneunit)
        cls.post_data = dict(name='posttestname',
                             value=345,
                             unit=cls.unit_url,
                             )
        cls.put_data = cls.post_data
        cls.patch_data = dict(name="test name")

    def setUp(self):
        super().setUp()
        self.obj = SolutionRatioOneUnitFactory(
            id=self.solutionratiooneunit,
            solution__id=self.solution,
            unit__id=self.unit,
            solution__solution_category__id=self.solutioncategory,
            solution__solution_category__user=self.uic,
            solution__user=self.uic,
            )
