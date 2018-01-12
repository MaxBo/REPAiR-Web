from django.test import TestCase
from django.core.validators import ValidationError

from repair.apps.login.models import (CaseStudy, UserInCasestudy)
from repair.apps.studyarea.models import (Stakeholder, StakeholderCategory)
from repair.tests.test import BasicModelTest, LoginTestCase
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
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

    #fixtures = ['changes_fixture.json', 'stakeholder_fixture.json']

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
        print(err.exception.messages)
