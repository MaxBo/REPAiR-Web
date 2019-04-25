
from django.urls import reverse
from test_plus import APITestCase
from repair.tests.test import BasicModelPermissionTest

from repair.apps.changes.factories import (
    SolutionCategoryFactory,
    SolutionFactory
)
from repair.apps.changes.models import Solution


class SolutioncategoryInKeyflowTest(BasicModelPermissionTest, APITestCase):

    casestudy = 17
    keyflow = 23
    solutioncategory = 21

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "solutioncategory"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflow)
        cls.url_pk = dict(pk=cls.solutioncategory)
        cls.post_data = dict(name='posttestname')
        cls.put_data = cls.post_data

    def setUp(self):
        super().setUp()
        self.obj = SolutionCategoryFactory(id=self.solutioncategory,
                                           keyflow=self.kic
                                           )

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


class SolutionInKeyflowTest(BasicModelPermissionTest,
                            APITestCase):

    casestudy = 17
    solutioncategory = 21
    solution = 36
    keyflow = 23

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.solutioncategory_url = cls.baseurl + \
            reverse('solutioncategory-detail',
                    kwargs=dict(pk=cls.solutioncategory,
                                casestudy_pk=cls.casestudy,
                                keyflow_pk=cls.keyflow))
        cls.url_key = "solution"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                            keyflow_pk=cls.keyflow)
        cls.url_pk = dict(pk=cls.solution)
        cls.post_data = dict(name='posttestname',
                             activities=[],
                             description="This is a description",
                             solution_category=cls.solutioncategory,
                             )
        cls.put_data = cls.post_data
        cls.patch_data = dict(name="test name")

    def setUp(self):
        super().setUp()
        self.obj = SolutionFactory(
            id=self.solution,
            solution_category__id=self.solutioncategory,
            solution_category__keyflow=self.kic
        )
