from django.test import TestCase
from django.core.validators import ValidationError


from repair.apps.studyarea.factories import (CaseStudyFactory,
                                             StakeholderCategoryFactory)



class UniqueStakeholderNames(TestCase):


    def test03_unique_stakeholdercategory(self):
        """Test the unique stakeholder name"""
        city1 = CaseStudyFactory(name='City1')
        city2 = CaseStudyFactory(name='City1')
        stakeholdercat1 = StakeholderCategoryFactory(
            casestudy=city1, name='Cat1')
        stakeholdercat2 = StakeholderCategoryFactory(
            casestudy=city1, name='Cat2')
        stakeholdercat3 = StakeholderCategoryFactory(
            casestudy=city2, name='Cat1')

        with self.assertRaisesMessage(
            ValidationError,
            'StakeholderCategory Cat1 already exists in casestudy City1',
            ) as err:
            stakeholdercat3 = StakeholderCategoryFactory(
                casestudy=city2, name='Cat1')
        print(err.exception.messages)
