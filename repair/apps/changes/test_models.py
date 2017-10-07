from django.test import TestCase


from .models import (CaseStudy,
                     Implementation,
                     Solution,
                     SolutionCategory,
                     SolutionInImplementationGeometry,
                     SolutionInImplementationNotes,
                     SolutionInImplementationQuantities,
                     SolutionQuantity,
                     SolutionRatioOneUnit,
                     Stakeholder,
                     StakeholderCategory,
                     Strategy,
                     UserAP12,
                     Unit,
                     UserAP34,
                     )


class ModelTest(TestCase):

    def test_string_representation(self):
        for Model in (CaseStudy,
                     Implementation,
                     Solution,
                     SolutionCategory,
                     SolutionQuantity,
                     SolutionRatioOneUnit,
                     Stakeholder,
                     StakeholderCategory,
                     Strategy,
                     Unit,
                     UserAP12,
                     UserAP34,
                     ):

            model = Model(name="MyName")
            self.assertEqual(str(model),"MyName")

    def test_repr_of_solutions_in_implementations(self):
        """Test the solutions in implementations"""
        solution = Solution(name='Sol1')
        implementation = Implementation(name='Impl2')

        #model = SolutionInImplementation(solution=solution,
                                         #implementation=implementation)
        #self.assertEqual(str(model), 'Sol1 in Impl2')

        model = SolutionInImplementationGeometry(
            solution=solution,
            implementation=implementation,
            name='Altona',
            geom='LatLon',
        )
        target = 'location Altona for Sol1 in Impl2 at LatLon'
        self.assertEqual(str(model), target)

        model = SolutionInImplementationNotes(
            solution=solution,
            implementation=implementation,
            note='An important Note'
        )
        target = 'Note for Sol1 in Impl2:\nAn important Note'
        self.assertEqual(str(model), target)


        quantity = SolutionQuantity(name='bins')
        model = SolutionInImplementationQuantities(
            solution=solution,
            implementation=implementation,
            quantity=quantity,
            value=42,
        )
        self.assertEqual(str(model), 'Sol1 in Impl2 has 42 bins')
