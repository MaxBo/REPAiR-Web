from django.test import TestCase
from django.core.validators import ValidationError
from django.contrib.gis.geos import LineString

from repair.apps.changes.models import (
    Strategy,
    Solution,
    SolutionCategory,
    SolutionInStrategy,
    SolutionInStrategyQuantity,
    SolutionQuantity,
    SolutionRatioOneUnit,
    Unit,
    )

from repair.apps.login.factories import UserInCasestudyFactory


class TestModelRepresentation(TestCase):

    def test_string_representation(self):
        for model_class in (Strategy,
                            Solution,
                            SolutionCategory,
                            SolutionRatioOneUnit,
                            Unit,
                            ):

            model = model_class(name="MyName")
            self.assertEqual(str(model), "MyName")

    def test_repr_of_solutions_in_implementations(self):
        """Test the solutions in implementations"""
        solution = Solution(name='Sol1')
        implementation = Strategy(name='Impl2')

        solution_in_impl = SolutionInStrategy(
            solution=solution,
            implementation=implementation)
        self.assertEqual(str(solution_in_impl), 'Sol1 in Impl2')

        unit = Unit(name='tons')
        quantity = SolutionQuantity(name='bins', unit=unit)
        self.assertEqual(str(quantity), 'bins [tons]')

        model = SolutionInStrategyQuantity(
            sii=solution_in_impl,
            quantity=quantity,
            value=42,
        )
        self.assertEqual(str(model), '42 bins [tons]')

