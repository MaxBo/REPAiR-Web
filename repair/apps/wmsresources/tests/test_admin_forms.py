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

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        wmsresource = WMSResourceFactory()
        casestudy = CaseStudyFactory()
        cls.add_data = dict(name = 'WMSResource30000',
                            uri = 'https://www.wms.nrw.de/gd/bohrungen')

    def test_form(self):
        add_data = dict(name = 'WMSResource300sff00',
                        uri = 'https://www.wms.nrw.de/gd/bohrungen')
        form = WMSForm(add_data)
        assert form.is_valid()
        form.save()
        wmsresource = WMSResource.objects.get(name=add_data['name'])
        assert wmsresource.layers is not None