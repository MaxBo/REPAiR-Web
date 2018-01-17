import json

from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
from rest_framework.test import APITestCase

from repair.apps.login.models import CaseStudy
from repair.apps.login.factories import *
import reversion


class ViewTest(APITestCase):

    fixtures = ['auth', 'sandbox']


    def test_get_group(self):
        url = reverse('group-list')
        data = {'name': 'MyGroup'}
        response = self.client.post(url, data, format='json')
        print(response)
        response = self.client.get(url)
        print(response.data)

    def test_get_user(self):
        lodz = reverse('casestudy-detail', kwargs=dict(pk=3))

        url = reverse('user-list')
        data = {'username': 'MyUser',
                'casestudies': [lodz],
                'password': 'PW',
                'organization': 'GGR',
                'groups': [],
                'email': 'a.b@c.de',}
        response = self.client.post(url, data, format='json')
        print(response)
        response = self.client.get(url)
        print(response.data)
        url = reverse('user-detail', kwargs=dict(pk=4))
        response = self.client.get(url)
        print(response.data)
        new_mail = 'new@mail.de'
        data = {'email': new_mail,}
        self.client.patch(url, data)
        response = self.client.get(url)
        assert response.data['email'] == new_mail


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
        client = Client()
        user = client.login(username=self.user1.user.username,
                            password=self.pw1)

        # ..and posts a new Casestudy
        url = reverse('casestudy-list')
        data = {'name': 'CS Version 1'}
        response = client.post(url, data)
        cs_id = response.data['id']
        client.logout()

        # user2 logs in
        user = client.login(username=self.user2.user.username,
                            password=self.pw2)

        url = reverse('casestudy-detail', kwargs={'pk': cs_id,})
        data = {'name': 'CS Version 2'}
        response = client.patch(url, json.dumps(data),
                                content_type='application/json')
        client.logout()

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

