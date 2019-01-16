import factory
from factory.django import DjangoModelFactory
from django.contrib.gis.geos.point import Point
from repair.apps.login.factories import (ProfileFactory,
                                         CaseStudyFactory,
                                         UserInCasestudyFactory)
from repair.apps.publications.factories import PublicationInCasestudyFactory

from . import models


class KeyflowFactory(DjangoModelFactory):
    class Meta:
        model = models.Keyflow
    name = 'PET Plastic'
    code = 'PET'

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
    note = 'A Keyflow in a Casestudy'
    keyflow = factory.SubFactory(KeyflowFactory)
    casestudy = factory.SubFactory(CaseStudyFactory)
    class Meta:
        model = models.KeyflowInCasestudy


class ReasonFactory(DjangoModelFactory):
    class Meta:
        model = models.Reason
    reason = 'Out of bounds'


class ProcessFactory(DjangoModelFactory):
    class Meta:
        model = models.Process
    name = 'subNACE process'

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
    activitygroup = factory.SubFactory(ActivityGroupFactory)


class ActorFactory(NodeFactory):
    class Meta:
        model = models.Actor
    name = factory.Sequence(lambda n: "Actor #%s" % n)
    consCode = 'ConsCode1'
    year = 2017
    turnover = 100000
    employees = 100
    BvDid = 'whatever'
    BvDii = 'BvDii99'
    website = 'www.example.com'
    activity = factory.SubFactory(ActivityFactory)
    reason = factory.SubFactory(ReasonFactory)


class FlowFactory(DjangoModelFactory):
    class Meta:
        model = models.Flow
    amount = 1234
    keyflow = factory.SubFactory(KeyflowInCasestudyFactory)


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = models.Product
    name = factory.Sequence(lambda n: "Product #%s" % n)
    nace = 'testnace'
    #default = True
    #keyflow = factory.SubFactory(KeyflowInCasestudyFactory)


class WasteFactory(DjangoModelFactory):
    class Meta:
        model = models.Waste
    name = factory.Sequence(lambda n: "Product #%s" % n)
    nace = 'testnace'
    ewc ='testewc'
    wastetype ='testtype'
    hazardous = False


class CompositionFactory(DjangoModelFactory):
    class Meta:
        model = models.Composition
    name = factory.Sequence(lambda n: "Composition #%s" % n)
    nace = '52.Retail'


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
    composition = factory.SubFactory(CompositionFactory)


class Actor2ActorFactory(FlowFactory):
    class Meta:
        model = models.Actor2Actor
    origin = factory.SubFactory(ActorFactory)
    destination = factory.SubFactory(ActorFactory)
    composition = factory.SubFactory(CompositionFactory)


class MaterialFactory(DjangoModelFactory):
    class Meta:
        model = models.Material
    name = factory.Sequence(lambda n: "Material #%s" % n)
    keyflow = None
    level = 1
    parent = None  #factory.SubFactory('repair.apps.asmfa.factories.MaterialFactory')


class StockFactory(FlowFactory):
    class Meta:
        model = models.Stock


class GroupStockFactory(FlowFactory):
    class Meta:
        model = models.GroupStock
    origin = factory.SubFactory(ActivityGroupFactory)
    #product = factory.SubFactory(ProductFactory)


class ActivityStockFactory(FlowFactory):
    class Meta:
        model = models.ActivityStock
    origin = factory.SubFactory(ActivityFactory)
    #product = factory.SubFactory(ProductFactory)


class ActorStockFactory(FlowFactory):
    class Meta:
        model = models.ActorStock
    origin = factory.SubFactory(ActorFactory)
    #product = factory.SubFactory(ProductFactory)


class GeolocationFactory(DjangoModelFactory):
    class Meta:
        model = models.Geolocation
    name = 'a location'
    address = 'MainStreet'
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


class ProductFractionFactory(DjangoModelFactory):
    class Meta:
        model = models.ProductFraction

    fraction = 10.2
    material = factory.SubFactory(MaterialFactory)
    composition = factory.SubFactory(CompositionFactory)
    publication = factory.SubFactory(PublicationInCasestudyFactory)
    avoidable = True



