from django.test import TestCase
from django.core.validators import ValidationError
from test_plus import APITestCase
from rest_framework import status

from repair.apps.login.models import (CaseStudy, UserInCasestudy)
from repair.apps.studyarea.models import (Stakeholder, StakeholderCategory)
from repair.tests.test import BasicModelTest, BasicModelReadTest
from django.urls import reverse
from repair.apps.changes.models import (
    Implementation,
    Solution,
    SolutionCategory,
    SolutionInImplementation,
    SolutionInImplementationGeometry,
    SolutionInImplementationNote,
    SolutionInImplementationQuantity,
    SolutionQuantity,
    SolutionRatioOneUnit,
    Strategy,
    Unit,
    )

from repair.apps.changes.factories import *


class StrategyInCasestudyTest(BasicModelTest, APITestCase):

    casestudy = 17
    strategy = 48
    userincasestudy = 67
    user = 99
    implementation = 43

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_url = cls.baseurl + \
            reverse('userincasestudy-detail',
                    kwargs=dict(pk=cls.userincasestudy,
                                casestudy_pk=cls.casestudy))
        cls.implementation_url = cls.baseurl + \
            reverse('implementation-detail',
                    kwargs=dict(pk=cls.implementation,
                                casestudy_pk=cls.casestudy))
        cls.url_key = "strategy"
        cls.url_pks = dict(casestudy_pk=cls.casestudy)
        cls.url_pk = dict(pk=cls.strategy)
        cls.post_data = dict(name='posttestname',
                             user=cls.user_url,
                             implementation_set=[cls.implementation_url])
        cls.put_data = cls.post_data
        cls.patch_data = dict(name="test name")

    def setUp(self):
        super().setUp()
        iic = ImplementationFactory(id=self.implementation,
                                    user=self.uic)
        self.obj = StrategyFactory(id=self.strategy,
                                   user=self.uic,
                                   implementations__id=self.implementation,
                                   )


class ModelTest(TestCase):

    fixtures = ['auth', 'sandbox']

    def test_string_representation(self):
        for Model in (CaseStudy,
                     Implementation,
                     Solution,
                     SolutionCategory,
                     SolutionRatioOneUnit,
                     Strategy,
                     Unit,
                     ):

            model = Model(name="MyName")
            self.assertEqual(str(model),"MyName")

    def test_repr_of_solutions_in_implementations(self):
        """Test the solutions in implementations"""
        solution = Solution(name='Sol1')
        implementation = Implementation(name='Impl2')

        solution_in_impl = SolutionInImplementation(
            solution=solution,
            implementation=implementation)
        self.assertEqual(str(solution_in_impl), 'Sol1 in Impl2')

        model = SolutionInImplementationGeometry(
            sii=solution_in_impl,
            name='Altona',
            geom='LatLon',
        )
        target = 'location Altona at LatLon'
        self.assertEqual(str(model), target)

        model = SolutionInImplementationNote(
            sii=solution_in_impl,
            note='An important Note'
        )
        target = 'Note for Sol1 in Impl2:\nAn important Note'
        self.assertEqual(str(model), target)

        unit = Unit(name='tons')
        quantity = SolutionQuantity(name='bins', unit=unit)
        self.assertEqual(str(quantity), 'bins [tons]')

        model = SolutionInImplementationQuantity(
            sii=solution_in_impl,
            quantity=quantity,
            value=42,
        )
        self.assertEqual(str(model), '42 bins [tons]')


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


class UniqueNames(TestCase):

    def test02_unique_strategy(self):
        """Test the unique strategy name"""
        user_city1 = UserInCasestudyFactory(casestudy__name='City1')
        user_city2 = UserInCasestudyFactory(casestudy__name='City2')

        # validate_unique is normally called when a form is validated
        strategy1_city1 = StrategyFactory(user=user_city1,
                                          name='FirstStrategy')
        strategy1_city2 = StrategyFactory(user=user_city2,
                                          name='FirstStrategy')
        strategy2_city1 = StrategyFactory(user=user_city1,
                                          name='SecondStrategy')
        with self.assertRaisesMessage(
            ValidationError,
            'Strategy FirstStrategy already exists in casestudy City1') as err:
            strategy1b_city1 = StrategyFactory(user=user_city1,
                                               name='FirstStrategy')


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
        self.obj = SolutionFactory(id=self.solution,
                                   solution_category__id=self.solutioncategory,
                                   solution_category__user=self.uic,
                                   user=self.uic,
                                   )


class SolutionquantityInSolutionInSolutioncategoryInCasestudyTest(BasicModelTest, APITestCase):

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
        #cls.solutioncategory_url = cls.baseurl + \
            #reverse('solutioncategory-detail',
                    #kwargs=dict(pk=cls.solutioncategory,
                                #casestudy_pk=cls.casestudy))
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
        self.obj = SolutionQuantityFactory(id=self.solutionquantity,
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
        self.obj = SolutionRatioOneUnitFactory(id=self.solutionratiooneunit,
                                               solution__id=self.solution,
                                               unit__id=self.unit,
                                               solution__solution_category__id=self.solutioncategory,
                                               solution__solution_category__user=self.uic,
                                               solution__user=self.uic,
                                               )


class ImplementationsInCasestudyTest(BasicModelTest, APITestCase):

    casestudy = 17
    user = 20
    userincasestudy = 21
    implementation = 30
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.usr_url = cls.baseurl + reverse('userincasestudy-detail',
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
                             geom="test geom")
        cls.put_data = dict(name="test name",
                             geom="test geom")
        cls.patch_data = dict(name="test name",
                             geom="test geom")


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
        #cls.post_data = dict(value=1000.12, quantity=cls.quantity_url)
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