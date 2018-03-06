# -*- coding: utf-8 -*-

from test_plus import APITestCase
from repair.tests.test import BasicModelReadPermissionTest

from repair.apps.wmsresources.factories import (
    WMSResourceInCasestudyFactory,
    WMSLayerFactory,
    LayerStyleFactory,
)


class WMSResourceInCaseStudyTest(BasicModelReadPermissionTest, APITestCase):

    casestudy = 1
    casestudy2 = 21
    wmsresource = 'MyWMSServiceProvider'
    user_id = 33
    casestudy1 = 11
    casestudy2 = 22

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.url_key = "wmsresourceincasestudy"
        cls.url_pks = dict(casestudy_pk=cls.casestudy)
        cls.url_pk = dict(pk=cls.wmsresource)

    def setUp(self):
        super().setUp()
        self.obj = WMSResourceInCasestudyFactory(
            casestudy=self.uic.casestudy,
            wmsresource__name=self.wmsresource)
        layer1 = WMSLayerFactory(wmsresource=self.obj.wmsresource)
        layer2 = WMSLayerFactory(wmsresource=self.obj.wmsresource)

        style1 = LayerStyleFactory(wmslayer=layer1)
        style2 = LayerStyleFactory(wmslayer=layer2)
        style22 = LayerStyleFactory(wmslayer=layer2)
