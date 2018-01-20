
from django.urls import reverse
from test_plus import APITestCase
from repair.tests.test import BasicModelTest

from repair.apps.changes.factories import (ImplementationFactory,
                                           StrategyFactory)


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
