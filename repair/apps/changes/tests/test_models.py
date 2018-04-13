from django.test import TestCase
from django.core.validators import ValidationError
from django.contrib.gis.geos import LineString

from repair.apps.changes.models import (
    Implementation,
    Solution,
    SolutionCategory,
    SolutionInImplementation,
    SolutionInImplementationQuantity,
    SolutionQuantity,
    SolutionRatioOneUnit,
    Strategy,
    Unit,
    )

from repair.apps.login.factories import UserInCasestudyFactory
from repair.apps.changes.factories import StrategyFactory


class TestModelRepresentation(TestCase):

    def test_string_representation(self):
        for model_class in (Implementation,
                            Solution,
                            SolutionCategory,
                            SolutionRatioOneUnit,
                            Strategy,
                            Unit,
                            ):

            model = model_class(name="MyName")
            self.assertEqual(str(model), "MyName")

    def test_repr_of_solutions_in_implementations(self):
        """Test the solutions in implementations"""
        solution = Solution(name='Sol1')
        implementation = Implementation(name='Impl2')

        solution_in_impl = SolutionInImplementation(
            solution=solution,
            implementation=implementation)
        self.assertEqual(str(solution_in_impl), 'Sol1 in Impl2')
        target = 'location Altona (LineString)'
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
