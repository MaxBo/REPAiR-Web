from django.test import TestCase
from django.test import Client
from repair.tests.test import AdminAreaTest
from repair.apps.login.models import User, CaseStudy
from repair.apps.wmsresources.models import WMSResourceInCasestudy, WMSResource
from django.contrib.admin.sites import AdminSite
from django.contrib.admin.options import ModelAdmin
from repair.apps.asmfa.factories import KeyflowInCasestudyFactory
from repair.apps.login.factories import CaseStudyFactory
from repair.apps.wmsresources.factories import WMSResourceFactory
from wms_client.admin import WMSForm
from repair.tests.test import AdminAreaTest

class WMSResourceAdminTest(AdminAreaTest, TestCase):
    """
    Test the admin area of WMSResources.
    """
    app = 'wms_client'
    model = 'wmsresource'
    form_class = WMSForm
    model_class = WMSResource
    check_feature = 'name'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        wmsresource = WMSResourceFactory()
        casestudy = CaseStudyFactory()
        cls.add_data = {'name': ['test_case'],
                        'uri': ['https://www.wms.nrw.de/gd/bohrungen']}
        cls.incomplete_data = {'name': ['test_incomplete_data'],}