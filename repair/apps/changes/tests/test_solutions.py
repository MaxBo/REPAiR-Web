
from django.urls import reverse
from test_plus import APITestCase
from repair.tests.test import BasicModelPermissionTest

from repair.apps.changes.factories import (
    SolutionCategoryFactory,
    SolutionFactory,
    SolutionQuantityFactory,
    SolutionRatioOneUnitFactory,
)
from repair.apps.changes.models import Solution
from repair.apps.login.factories import UserInCasestudyFactory


class SolutioncategoryInCasestudyTest(BasicModelPermissionTest, APITestCase):

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

    def test_casestudy_solutioncategories(self):
        """Test the casestudy.solutioncategories property"""
        solcat1 = self.obj
        solcat2 = SolutionCategoryFactory(user=self.uic,
                                          name='SolCat2')
        user2 = UserInCasestudyFactory(casestudy=self.uic.casestudy)
        solcat3 = SolutionCategoryFactory(user=user2,
                                          name='SolCat3')

        solution_categories = user2.casestudy.solution_categories
        self.assertSetEqual(solution_categories, {solcat1,
                                                  solcat2,
                                                  solcat3})

    def test_protection_of_deletion(self):
        """
        Test if the protection of objects, that are referred to
        by a foreign key using the view works and if the deletion on the model
        with cascade works too.
        """
        # generate a new solution category with 2 solutions
        solcat_id = 44
        solcat2 = SolutionCategoryFactory(id=solcat_id)
        solution2 = SolutionFactory(solution_category=solcat2,
                                    name='Protected Solution')
        solution3 = SolutionFactory(solution_category=solcat2,
                                    name='Another Solution')

        # try to delete using the view
        url = self.url_key + '-detail'
        kwargs = {**self.url_pks, 'pk': solcat2.pk, }
        response = self.delete(url, **kwargs)

        # this should raise an ProtectedError
        self.response_403()
        assert b'Cannot delete some instances of model' in response.content
        assert b'Solution: Protected Solution' in response.content
        assert b'Solution: Another Solution' in response.content

        # deletion on the model will delete the solution category and
        # cascadedly the referencing solution
        qs = Solution.objects.filter(solution_category__id=solcat_id)
        assert len(qs) == 2
        solcat2.delete()
        qs = Solution.objects.filter(solution_category__id=solcat_id)
        assert not qs


class SolutionInSolutioncategoryInCasestudyTest(BasicModelPermissionTest,
                                                APITestCase):

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
        user = cls.baseurl + reverse('userincasestudy-detail',
                                     kwargs=dict(pk=cls.uic.id,
                                                 casestudy_pk=cls.casestudy))
        cls.post_data = dict(name='posttestname',
                             activities=[],
                             user=user,
                             description="This is a description",
                             one_unit_equals='20',
                             solution_category=cls.solutioncategory,
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
    BasicModelPermissionTest, APITestCase):

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
                             unit=cls.unit,
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


class SolutionratiooneunitInSolutionInSolutioncategoryInCasestudyTest(
    BasicModelPermissionTest, APITestCase):

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
                             unit=cls.unit,
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
