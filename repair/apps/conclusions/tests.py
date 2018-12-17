# -*- coding: utf-8 -*-
from django.urls import reverse
from test_plus import APITestCase
from rest_framework import status
import factory
from factory.django import DjangoModelFactory
from repair.apps.login.factories import CaseStudyFactory
from repair.apps.asmfa.factories import KeyflowInCasestudyFactory

from repair.tests.test import BasicModelPermissionTest, LoginTestCase
from repair.apps.conclusions.models import Conclusion, ConsensusLevel, Section


class ConsensusLevelFactory(DjangoModelFactory):
    casestudy = factory.SubFactory(CaseStudyFactory)
    name = 'level name'

    class Meta:
        model = ConsensusLevel


class SectionFactory(DjangoModelFactory):
    casestudy = factory.SubFactory(CaseStudyFactory)
    name = 'section name'

    class Meta:
        model = Section


class ConclusionFactory(DjangoModelFactory):
    keyflow = factory.SubFactory(KeyflowInCasestudyFactory)
    text = 'bla'
    link = ''
    image = None
    consensus_level = factory.SubFactory(ConsensusLevelFactory)
    section = factory.SubFactory(SectionFactory)
    step = 1

    class Meta:
        model = Conclusion


class ConsensusLevelTest(BasicModelPermissionTest, APITestCase):

    casestudy = 17
    level = 2

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "consensuslevel"
        cls.url_pks = dict(casestudy_pk=cls.casestudy)
        cls.url_pk = dict(pk=cls.level)
        cls.post_data = dict(name='123')
        cls.put_data = cls.post_data
        cls.patch_data = cls.post_data

    def setUp(self):
        super().setUp()
        self.obj = ConsensusLevelFactory(casestudy=self.uic.casestudy,
                                         id=self.level)


class SectionTest(BasicModelPermissionTest, APITestCase):

    casestudy = 17
    section = 1

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "section"
        cls.url_pks = dict(casestudy_pk=cls.casestudy)
        cls.url_pk = dict(pk=cls.section)
        cls.post_data = dict(name='123')
        cls.put_data = cls.post_data
        cls.patch_data = cls.post_data

    def setUp(self):
        super().setUp()
        self.obj = SectionFactory(casestudy=self.uic.casestudy,
                                  id=self.section)


class ConclusionTest(BasicModelPermissionTest, APITestCase):

    conclusion = 3

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "conclusion"
        cls.url_pks = dict(casestudy_pk=cls.uic.casestudy.id,
                           keyflow_pk=cls.kic.id)
        cls.url_pk = dict(pk=cls.conclusion)

        consensus = ConsensusLevelFactory(name='whatever',
                                          casestudy=cls.uic.casestudy)
        section = SectionFactory(name='iamsection',
                                 casestudy=cls.uic.casestudy)

        cls.post_data = dict(text='1342243', link='www.google.de',
                             consensus_level=consensus.id, section=section.id,
                             step=2)
        cls.put_data = cls.post_data
        cls.patch_data = cls.post_data

    def setUp(self):
        super().setUp()
        self.obj = ConclusionFactory(keyflow=self.kic,
                                     id=self.conclusion)
