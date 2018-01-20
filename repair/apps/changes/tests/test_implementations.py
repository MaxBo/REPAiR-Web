from django.test import TestCase
from django.urls import reverse
from test_plus import APITestCase
from django.contrib.gis.geos import Point, MultiPoint, LineString

from repair.tests.test import BasicModelTest, BasicModelReadTest
from repair.apps.changes.models import (
    SolutionInImplementationQuantity,
    SolutionQuantity,
    )

from repair.apps.changes.factories import (
    SolutionFactory,
    SolutionQuantityFactory,
    ImplementationFactory,
    SolutionInImplementationFactory,
    SolutionInImplementationGeometryFactory,
    SolutionInImplementationNoteFactory,
    SolutionInImplementationQuantityFactory)


class ImplementationsInCasestudyTest(BasicModelTest, APITestCase):

    casestudy = 17
    user = 20
    userincasestudy = 21
    implementation = 30

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.usr_url = cls.baseurl + reverse(
            'userincasestudy-detail',
            kwargs=dict(pk=cls.userincasestudy,
                        casestudy_pk=cls.casestudy))
        cls.sol_set = []
        cls.url_key = "implementation"
        cls.url_pks = dict(casestudy_pk=cls.casestudy)
        cls.url_pk = dict(pk=cls.implementation)
        cls.post_data = dict(name="Test Implementation",
                             user=cls.usr_url,
                             solution_set=cls.sol_set)
        cls.put_data = dict(name="Test Implementation",
                            user=cls.usr_url,
                            solution_set=cls.sol_set)
        cls.patch_data = dict(name="Test Implementation")

    def setUp(self):
        super().setUp()
        self.obj = ImplementationFactory(id=self.implementation,
                                         user=self.uic)


class ModelSolutionInImplementation(TestCase):

    def test01_new_solutionininplementation(self):
        """Test the new solution implementation"""

        # Create a solution with two quantities
        solution = SolutionFactory()
        solution_quantity1 = SolutionQuantityFactory(
            solution=solution, name='q1')
        solution_quantity2 = SolutionQuantityFactory(
            solution=solution, name='q2')

        # add solution to an implementation
        implementation = ImplementationFactory()
        solution_in_impl = SolutionInImplementationFactory(
            solution=solution,
            implementation=implementation)

        # check, if the SolutionInImplementationQuantity contains
        # now the 2 quantities

        solution_in_impl_quantities = SolutionInImplementationQuantity.\
            objects.filter(sii=solution_in_impl)
        solution_names = solution_in_impl_quantities.values_list(
            'quantity__name', flat=True)
        assert len(solution_names) == 2
        assert set(solution_names) == {'q1', 'q2'}

        # create a solution that requires 3 quantities

        # add to the solution a third quantity
        solution_quantity3 = SolutionQuantityFactory(solution=solution,
                                                     name='q3')

        # check if the new quantity has been added to the related table
        solution_in_impl_quantities = SolutionInImplementationQuantity.\
            objects.filter(sii=solution_in_impl)
        solution_names = solution_in_impl_quantities.values_list(
            'quantity__name', flat=True)
        assert len(solution_names) == 3
        assert set(solution_names) == {'q1', 'q2', 'q3'}

        # remove a solution quantity
        to_delete = SolutionQuantity.objects.filter(solution=solution,
                                                    name='q2')
        solution_id, deleted = to_delete.delete()
        # assert that 1 row in changes.SolutionInImplementationQuantity
        # are deleted
        assert deleted.get('changes.SolutionInImplementationQuantity') == 1

        # check the related SolutionInImplementationQuantity
        solution_in_impl_quantities = SolutionInImplementationQuantity.\
            objects.filter(sii=solution_in_impl)
        solution_names = solution_in_impl_quantities.values_list(
            'quantity__name', flat=True)
        assert len(solution_names) == 2
        assert set(solution_names) == {'q1', 'q3'}

        # remove the solution_in_implementation
        sii_id, deleted = solution_in_impl.delete()
        # assert that 2 rows in changes.SolutionInImplementationQuantity
        # are deleted
        assert deleted.get('changes.SolutionInImplementationQuantity') == 2
        solution_in_impl_quantities = SolutionInImplementationQuantity.\
            objects.filter(sii=sii_id)
        assert not solution_in_impl_quantities


class SolutionInImplementationInCasestudyTest(BasicModelTest, APITestCase):

    casestudy = 17
    user = 20
    implementation = 30
    solution = 20
    solutioncategory = 56
    solution_implementation = 40

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.solution_url = cls.baseurl + \
            reverse('solution-detail',
                    kwargs=dict(casestudy_pk=cls.casestudy,
                                solutioncategory_pk=cls.solutioncategory,
                                pk=cls.solution))
        cls.implementation_url = cls.baseurl + \
            reverse('implementation-detail',
                    kwargs=dict(casestudy_pk=cls.casestudy,
                                pk=cls.implementation))
        cls.post_urls = [cls.solution_url, cls.implementation_url]
        cls.sol_set = []
        cls.url_key = "solutioninimplementation"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           implementation_pk=cls.implementation)
        cls.url_pk = dict(pk=cls.solution)
        cls.post_data = dict(solution=cls.solution_url,
                             implementation=cls.implementation_url)
        cls.put_data = dict(solution=cls.solution_url,
                            implementation=cls.implementation_url)
        cls.patch_data = dict(solution=cls.solution_url,
                              implementation=cls.implementation_url)

    def setUp(self):
        super().setUp()
        self.obj = SolutionInImplementationFactory(
            solution__user=self.uic,
            solution__solution_category__user=self.uic,
            solution__id=self.solution,
            implementation__user=self.uic,
            implementation__id=self.implementation,
            solution__solution_category__id=self.solutioncategory,
            id=self.solution_implementation)


class GeometryInSolutionInImplementationInCasestudyTest(BasicModelTest,
                                                        APITestCase):

    casestudy = 17
    user = 20
    implementation = 30
    solution = 20
    solutioncategory = 56
    solution_implementation = 40
    geometry = 25

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sol_set = []
        cls.url_key = "solutioninimplementationgeometry"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           implementation_pk=cls.implementation,
                           solution_pk=cls.solution_implementation)
        cls.url_pk = dict(pk=cls.geometry)
        cls.post_data = dict(name="test name",
                             geom=Point(5, 6, srid=4326).geojson)
        cls.put_data = dict(name="test name",
                            geom=MultiPoint([Point(5, 6, srid=4326),
                                             Point(7, 8, srid=4326)]).geojson)
        cls.patch_data = dict(name="test name",
                              geom=LineString([(1, 1), (2, 2)]).geojson)

    def setUp(self):
        super().setUp()
        self.obj = SolutionInImplementationGeometryFactory(
            sii__solution__user=self.uic, sii__solution__id=self.solution,
            sii__implementation__user=self.uic,
            sii__implementation__id=self.implementation,
            sii__solution__solution_category__id=self.solutioncategory,
            sii__id=self.solution_implementation,
            id=self.geometry)


class NoteInSolutionInImplementationInCasestudyTest(BasicModelTest,
                                                    APITestCase):

    casestudy = 17
    user = 20
    implementation = 30
    solution = 20
    solutioncategory = 56
    solution_implementation = 40
    note = 25

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sol_set = []
        cls.url_key = "solutioninimplementationnote"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           implementation_pk=cls.implementation,
                           solution_pk=cls.solution_implementation)
        cls.url_pk = dict(pk=cls.note)
        cls.post_data = dict(note="test note")
        cls.put_data = dict(note="test note")
        cls.patch_data = dict(note="test note")

    def setUp(self):
        super().setUp()
        self.obj = SolutionInImplementationNoteFactory(
            sii__solution__user=self.uic, sii__solution__id=self.solution,
            sii__implementation__user=self.uic,
            sii__implementation__id=self.implementation,
            sii__solution__solution_category__id=self.solutioncategory,
            sii__id=self.solution_implementation,
            id=self.note)


class QuantityInSolutionInImplementationInCasestudyTest(BasicModelReadTest,
                                                        APITestCase):
    """
    Test is not working:
    - delete is not allowed
    - post is not possible via Browser api
    """
    casestudy = 17
    user = 20
    implementation = 30
    solution = 20
    solutioncategory = 56
    solution_implementation = 40
    quantity = 25

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sol_set = []
        cls.url_key = "solutioninimplementationquantity"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           implementation_pk=cls.implementation,
                           solution_pk=cls.solution_implementation)
        cls.quantity_url = cls.baseurl + \
            reverse('solutionquantity-detail',
                    kwargs=dict(casestudy_pk=cls.casestudy,
                                solutioncategory_pk=cls.solutioncategory,
                                solution_pk=cls.solution,
                                pk=cls.quantity))
        cls.post_urls = [cls.quantity_url]
        cls.url_pk = dict(pk=cls.quantity)
        cls.put_data = dict(value=1000.12)
        cls.patch_data = dict(value=222.333)

    def setUp(self):
        super().setUp()
        self.obj = SolutionInImplementationQuantityFactory(
            sii__solution__user=self.uic, sii__solution__id=self.solution,
            sii__implementation__user=self.uic,
            sii__implementation__id=self.implementation,
            sii__solution__solution_category__id=self.solutioncategory,
            sii__id=self.solution_implementation,
            id=self.quantity)
