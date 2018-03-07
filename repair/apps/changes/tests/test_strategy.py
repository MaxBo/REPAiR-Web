
from django.urls import reverse
from test_plus import APITestCase
from repair.tests.test import BasicModelPermissionTest

from repair.apps.changes.factories import (ImplementationFactory,
                                           StrategyFactory)

from repair.apps.studyarea.factories import StakeholderFactory


class StrategyInCasestudyTest(BasicModelPermissionTest, APITestCase):

    casestudy = 17
    strategy = 48
    userincasestudy = 67
    user = 99
    implementation = 43
    stakeholder = 99
    stakeholdercategory = 66

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
        cls.stakeholder_url = cls.baseurl + reverse(
            'stakeholder-detail',
            kwargs=dict(pk=cls.stakeholder,
                        casestudy_pk=cls.casestudy,
                        stakeholdercategory_pk=cls.stakeholdercategory)
            )

        cls.url_key = "strategy"
        cls.url_pks = dict(casestudy_pk=cls.casestudy)
        cls.url_pk = dict(pk=cls.strategy)
        cls.post_data = dict(name='posttestname',
                             user=cls.user_url,
                             implementation_set=[cls.implementation_url],
                             coordinator=cls.stakeholder_url)
        cls.put_data = dict(name='puttestname',
                            user=cls.user_url,
                            implementation_set=[cls.implementation_url],
                            coordinator=cls.stakeholder_url)
        cls.patch_data = dict(name="test name")

    def setUp(self):
        super().setUp()
        iic = ImplementationFactory(id=self.implementation,
                                    user=self.uic)
        self.obj = StrategyFactory(id=self.strategy,
                                   user=self.uic,
                                   implementations__id=self.implementation,
                                   )
        self.stakeholder = StakeholderFactory(
            id=self.stakeholder,
            stakeholder_category__id=self.stakeholdercategory,
            stakeholder_category__casestudy=self.uic.casestudy)
