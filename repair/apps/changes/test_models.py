from django.test import TestCase


from .models import (CaseStudy,
                     Implementation,
                     Solution,
                     SolutionCategory,
                     SolutionInImplementation,
                     SolutionInImplementationGeometry,
                     SolutionInImplementationNote,
                     SolutionInImplementationQuantity,
                     SolutionQuantity,
                     SolutionRatioOneUnit,
                     Stakeholder,
                     StakeholderCategory,
                     Strategy,
                     Unit,
                     User,
                     UserInCasestudy,
                     )


class ModelTest(TestCase):

    fixtures = ['changes_fixture.json',]

    def test_string_representation(self):
        for Model in (CaseStudy,
                     Implementation,
                     Solution,
                     SolutionCategory,
                     SolutionRatioOneUnit,
                     Stakeholder,
                     StakeholderCategory,
                     Strategy,
                     Unit,
                     User,
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
        target = 'location Altona for Sol1 in Impl2 at LatLon'
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
        self.assertEqual(str(model), 'Sol1 in Impl2 has 42 bins [tons]')

    def test_unique_names(self):
        """test unique names"""
        city1 = CaseStudy(name='City1')
        city2 = CaseStudy(name='City2')
        user1 = User(name='User1')
        user2 = User(name='User2')
        #user1.casestudies.add(city1)
        #user1.casestudies.add(city2)
        #user2.casestudies.add(city2)

        user1city1 = UserInCasestudy(user=user1, casestudy=city1)
        user1city2 = UserInCasestudy(user=user1, casestudy=city2)
        user2city2 = UserInCasestudy(user=user2, casestudy=city2)

        Strategy11 = Strategy(name='Strategy', user=user1city1)
        Strategy12 = Strategy(name='Strategy', user=user1city2)
        Strategy22 = Strategy(name='Strategy', user=user2city2)

