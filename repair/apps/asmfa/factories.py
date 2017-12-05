import factory
from factory.django import DjangoModelFactory
from django.contrib.gis.geos.point import Point
from repair.apps.login.factories import (ProfileFactory,
                                         CaseStudyFactory,
                                         UserInCasestudyFactory)

from . import models


class DataEntryFactory(DjangoModelFactory):
    class Meta:
        model = models.DataEntry
    source = 'data'
    user = factory.SubFactory(ProfileFactory)


class KeyflowFactory(DjangoModelFactory):
    class Meta:
        model = models.Keyflow
    name = 'PET Plastic'
    code = 'PET'

    #casestudy = factory.SubFactory(CaseStudyFactory)

    @factory.post_generation
    def casestudies(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of casestudies were passed in, use them
            for casestudy in extracted:
                self.casestudies.add(casestudy)



class KeyflowInCasestudyFactory(DjangoModelFactory):
    class Meta:
        model = models.KeyflowInCasestudy
    note = 'A Keyflow in a Casestudy'
    keyflow = factory.SubFactory(KeyflowFactory)
    casestudy = factory.SubFactory(CaseStudyFactory)


class QualityFactory(DjangoModelFactory):
    class Meta:
        model = models.Quality
    name = 'Best Quality'


class NodeFactory(DjangoModelFactory):
    class Meta:
        model = models.Node


class ActivityGroupFactory(NodeFactory):
    class Meta:
        model = models.ActivityGroup
    name = factory.Sequence(lambda n: "ActivityGroup #%s" % n)
    code = Meta.model.activity_group_choices[0]
    keyflow = factory.SubFactory(KeyflowInCasestudyFactory)


class ActivityFactory(NodeFactory):
    class Meta:
        model = models.Activity
    name = factory.Sequence(lambda n: "Activity #%s" % n)
    nace = '52.Retail'
    #keyflow = factory.SubFactory(KeyflowInCasestudyFactory)
    activitygroup = factory.SubFactory(ActivityGroupFactory)


class ActorFactory(NodeFactory):
    class Meta:
        model = models.Actor
    name = factory.Sequence(lambda n: "Actor #%s" % n)
    consCode = 'ConsCode1'
    year = 2017
    turnover = 100000
    employees = 100
    BvDii = 'BvDii99'
    website = 'www.example.com'
    activity = factory.SubFactory(ActivityFactory)


class FlowFactory(DjangoModelFactory):
    class Meta:
        model = models.Flow
    amount = 1234
    keyflow = factory.SubFactory(KeyflowInCasestudyFactory)
    quality = factory.SubFactory(QualityFactory)


class Group2GroupFactory(FlowFactory):
    class Meta:
        model = models.Group2Group
    origin = factory.SubFactory(ActivityGroupFactory)
    destination = factory.SubFactory(ActivityGroupFactory)


class Activity2ActivityFactory(FlowFactory):
    class Meta:
        model = models.Activity2Activity
    origin = factory.SubFactory(ActivityFactory)
    destination = factory.SubFactory(ActivityFactory)


class Actor2ActorFactory(FlowFactory):
    class Meta:
        model = models.Actor2Actor
    origin = factory.SubFactory(ActorFactory)
    destination = factory.SubFactory(ActorFactory)


class StockFactory(FlowFactory):
    class Meta:
        model = models.Stock


class GroupStockFactory(FlowFactory):
    class Meta:
        model = models.GroupStock
    origin = factory.SubFactory(ActivityGroupFactory)


class ActivityStockFactory(FlowFactory):
    class Meta:
        model = models.ActivityStock
    origin = factory.SubFactory(ActivityFactory)


class ActorStockFactory(FlowFactory):
    class Meta:
        model = models.ActorStock
    origin = factory.SubFactory(ActorFactory)


class GeolocationFactory(DjangoModelFactory):
    class Meta:
        model = models.Geolocation
    note = 'a location'
    address = 'MainStreet'
    building = '12'
    postcode = '12345'
    city = 'Sevilla'
    country = 'Spain'
    geom = Point(x=11.1, y=12.2, srid=4326)


class AdministrativeLocationFactory(GeolocationFactory):
    class Meta:
        model = models.AdministrativeLocation
    actor = factory.SubFactory(ActorFactory)


class OperationalLocationFactory(AdministrativeLocationFactory):
    class Meta:
        model = models.OperationalLocation
    employees = 123
    turnover = 98765.43
