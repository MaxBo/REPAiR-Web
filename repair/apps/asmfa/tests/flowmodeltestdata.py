# -*- coding: utf-8 -*-
from collections import namedtuple
import numpy as np


from repair.apps.asmfa.factories import (KeyflowInCasestudyFactory,
                                         Actor2ActorFactory,
                                         MaterialFactory,
                                         ProductFractionFactory,
                                         ActorFactory,
                                         ActivityFactory,
                                         WasteFactory,
                                         ProductFactory,
                                         ActorStockFactory,
                                         )
from repair.apps.publications.factories import PublicationInCasestudyFactory

from repair.apps.asmfa.models import Actor, Material, Actor2Actor


class GenerateTestDataMixin:
    """
    Generate Testdata
    """

    def create_keyflow(self):
        """Create the keyflow"""
        self.keyflow_id = 1
        self.kic = KeyflowInCasestudyFactory(id=self.keyflow_id)
        self.pub = PublicationInCasestudyFactory(casestudy=self.kic.casestudy)

    def create_materials(self):
        """Create the materials, compositions and fractions"""
        Mat = namedtuple('Mat', ['name', 'is_waste'])
        Mat.__new__.__defaults__ = (None, False)
        self.materials = {}
        self.compositions = {}
        self.fractions = {}
        material_names = [Mat('Plastic', is_waste=True),
                          Mat('Crude Oil'),
                          Mat('Petrol'),
                          Mat('Milk'),
                          Mat('Cucumber'),
                          Mat('Human Waste', is_waste=True),
                          Mat('Other Waste', is_waste=True),
                          ]
        for mat in material_names:
            material = MaterialFactory(
                name=mat.name,
                keyflow=self.kic)
            self.materials[mat.name] = material
            Factory = WasteFactory if mat.is_waste else ProductFactory
            composition = Factory(name=mat.name)
            self.compositions[mat.name] = composition
            fraction = ProductFractionFactory(
                fraction=1,
                material=material,
                composition=composition,
                publication=self.pub,
            )
            self.fractions[mat.name] = fraction

    def create_actors(self):
        """Create the actors"""
        activity_names = ['oil_rig',
                          'oil_refinery',
                          'production',
                          'recycling',
                          'consumption',
                          'packaging',
                          'farm',
                          'burn',
                          'waste',
                          'waste_2']
        self.actors = {}
        for activity_name in activity_names:
            self.actors[activity_name] = ActorFactory(
                name=activity_name,
                activity__name=activity_name,
                activity__activitygroup__keyflow=self.kic)

    def create_flows(self):
        """Create the flows"""
        Flow = namedtuple('Flow', ['origin',
                                   'destination',
                                   'material',
                                   'amount'])
        Flow.__new__.__defaults__ = (None, None, None, 0)
        flows = [
            Flow('oil_rig', 'oil_refinery', 'Crude Oil', 1000),
            Flow('oil_refinery', 'production', 'Plastic'),
            Flow('oil_refinery', 'oil_refinery_stock', 'Petrol'),
            Flow('production', 'packaging', 'Plastic'),
            Flow('farm', 'packaging', 'Cucumber'),
            Flow('farm', 'packaging', 'Milk'),
            Flow('packaging', 'consumption', 'Plastic'),
            Flow('packaging', 'consumption', 'Cucumber'),
            Flow('packaging', 'consumption', 'Milk'),
            Flow('consumption', 'waste', 'Human Waste'),
            Flow('consumption', 'waste_2', 'Other Waste'),
            Flow('consumption', 'burn', 'Plastic'),
            Flow('consumption', 'recycling', 'Plastic'),
            Flow('recycling', 'production', 'Plastic'),
            Flow('recycling', 'recycling_stock', 'Plastic'),
        ]

        for flow in flows:
            origin = Actor.objects.get(name=flow.origin)
            material = Material.objects.get(name=flow.material)
            composition = self.compositions[material.name]
            if flow.destination.endswith('_stock'):
                stock = ActorStockFactory(origin=origin,
                                          composition=composition,
                                          keyflow=self.kic,
                                          amount=flow.amount)
            else:
                destination = Actor.objects.get(name=flow.destination)
                actor2actor = Actor2ActorFactory(origin=origin,
                                                 destination=destination,
                                                 composition=composition,
                                                 keyflow=self.kic,
                                                 amount=flow.amount,
                                                 )


class GenerateBigTestDataMixin(GenerateTestDataMixin):
    """Big amount of Test Data"""
    def create_actors(self, n_actors=10000):
        activity_names = [
            'production',
            'recycling',
            'consumption',
        ]
        self.activities = {}
        for activity_name in activity_names:
            self.activities[activity_name] = ActivityFactory(
                name=activity_name,
                activitygroup__keyflow=self.kic)

        activities = np.random.choice(list(self.activities.values()),
                                      n_actors)
        actors = [Actor(activity=activities[i],
                        name=['Actor_{}'.format(i)],
                        )
                  for i in range(n_actors)]
        Actor.objects.bulk_create(actors)

    def create_flows(self, n_flows=10000):
        """Create big amounts of flows"""
        composition = self.compositions['Plastic']
        actors = Actor.objects.all()
        origins = np.random.choice(actors, n_flows)
        destinations = np.random.choice(actors, n_flows)
        amounts = np.random.randint(1, 1000, (n_flows, ))
        flows = [Actor2Actor(origin=origins[i],
                             destination=destinations[i],
                             composition=composition,
                             keyflow=self.kic,
                             amount=amounts[i],
                             )
                 for i in range(n_flows)]
        Actor2Actor.objects.bulk_create(flows)
