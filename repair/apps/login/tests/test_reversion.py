import json

from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
from test_plus import APITestCase
import reversion

from repair.apps.login.models import CaseStudy, UserInCasestudy
from repair.apps.login.factories import *


class TestReversionOfCasestudy(APITestCase):

    def setUp(self):
        self.pw1 = 'ABCD'
        self.pw2 = 'EFGH'
        self.user1 = ProfileFactory(user__username='User1',
                                    user__password=self.pw1)
        self.user2 = ProfileFactory(user__username='User2',
                                    user__password=self.pw2)


    def test01_casestudy_reversion(self):
        """Test the versioning of casestudies"""

        # Declare a revision block.
        with reversion.create_revision():

            # Save a new model instance.
            obj = CaseStudy(name="Casestudy Version 1")
            obj.save()

            # Store some meta-information.
            reversion.set_user(self.user1.user)
            reversion.set_comment("Created revision 1")

        # Declare a new revision block.
        with reversion.create_revision():

            # Update the model instance.
            obj.name = "Casestudy Version 2"
            obj.save()

            # Store some meta-information.
            reversion.set_user(self.user2.user)
            reversion.set_comment("Created revision 2")

        # Load a queryset of versions for a specific model instance.
        versions = reversion.models.Version.objects.get_for_object(obj)
        assert len(versions) == 2

        # Check the serialized data for the first version.
        assert versions[1].field_dict["name"] == "Casestudy Version 1"
        assert versions[1].revision.user == self.user1.user

        # Check the serialized data for the second version.
        assert versions[0].field_dict["name"] == "Casestudy Version 2"
        assert versions[0].revision.user == self.user2.user

    def test02_casestudy_reversion_view(self):
        """Test the view for versioning of casestudies"""
        # user1 logs in
        #client = Client()
        user = self.client.login(username=self.user1.user.username,
                            password=self.pw1)

        # ..and posts a new Casestudy
        #url = reverse('casestudy-list')
        data = {'name': 'CS Version 1'}
        response = self.post('casestudy-list', data=data)
        cs_id = response.data['id']
        self.client.logout()

        # add the 2nd user to the casestudy
        casestudy = CaseStudy.objects.get(id=cs_id)
        uic = UserInCasestudy(user=self.user2, casestudy=casestudy)
        uic.save()

        # user2 logs in
        user = self.client.login(username=self.user2.user.username,
                                 password=self.pw2)

        #url = reverse('casestudy-detail', kwargs={'pk': cs_id,})
        data = {'name': 'CS Version 2'}
        response = self.patch('casestudy-detail', pk=cs_id,
                              data=json.dumps(data),
                              extra=dict(content_type='application/json'))
        self.client.logout()

        obj = CaseStudy.objects.get(pk=cs_id)
        # Load a queryset of versions for a specific model instance.
        versions = reversion.models.Version.objects.get_for_object(obj)
        assert len(versions) == 2

        # Check the serialized data for the first version.
        assert versions[1].field_dict["name"] == "CS Version 1"
        assert versions[1].revision.user == self.user1.user

        # Check the serialized data for the second version.
        assert versions[0].field_dict["name"] == "CS Version 2"
        assert versions[0].revision.user == self.user2.user

