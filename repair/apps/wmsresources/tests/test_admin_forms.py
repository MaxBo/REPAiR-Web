from django.test import TestCase
from repair.tests.test import AdminAreaTest
from repair.apps.wmsresources.models import WMSResource
from repair.apps.login.factories import CaseStudyFactory
from repair.apps.wmsresources.factories import WMSResourceFactory
from wms_client.admin import WMSForm


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
                        'uri': ['https://monitor.ioer.de/cgi-bin/wms?MAP=O06RG_wms']}
        cls.incomplete_data = {'name': ['test_incomplete_data'],}