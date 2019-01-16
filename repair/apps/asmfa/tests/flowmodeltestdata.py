# -*- coding: utf-8 -*-
from collections import namedtuple


from repair.apps.asmfa.factories import (KeyflowInCasestudyFactory,
                                         Actor2ActorFactory,
                                         MaterialFactory,
                                         ProductFractionFactory,
                                         ActorFactory,
                                         WasteFactory,
                                         ProductFactory,
                                         ActorStockFactory,
                                         )
from repair.apps.publications.factories import PublicationInCasestudyFactory

from repair.apps.asmfa.models import Actor, Material


class GenerateTestDataMixin:
    """
    Generate Testdata
    """
    def setUp(self):
        super().setUp()
        self.create_keyflow()
        self.create_materials()
        self.create_actors()
        self.create_flows()

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
