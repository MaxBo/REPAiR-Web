# -*- coding: utf-8 -*-
from collections import namedtuple
import numpy as np
from django.test import TestCase

from repair.apps.asmfa.factories import (KeyflowInCasestudyFactory,
                                         Actor2ActorFactory,
                                         MaterialFactory,
                                         ProductFractionFactory,
                                         ActorFactory,
                                         ActivityFactory,
                                         WasteFactory,
                                         ProductFactory,
                                         ActorStockFactory,
                                         ProcessFactory,
                                         ActivityGroupFactory,
                                         FractionFlowFactory
                                         )
from repair.apps.publications.factories import PublicationInCasestudyFactory

from repair.apps.asmfa.models import Actor, Material, Actor2Actor

class GenerateBreadToBeerData(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.keyflow = KeyflowInCasestudyFactory(id=2)
        cls.pub = PublicationInCasestudyFactory(casestudy=cls.keyflow.casestudy)

        ## Materials ##

        bread = MaterialFactory(name='bread',
                                keyflow=cls.keyflow)
        beer = MaterialFactory(name='beer',
                               keyflow=cls.keyflow)
        barley = MaterialFactory(name='barley',
                                 keyflow=cls.keyflow)
        sludge = MaterialFactory(name='sludge',
                                 keyflow=cls.keyflow)
        other_waste = MaterialFactory(name='other waste',
                                      keyflow=cls.keyflow)

        ## Processes ##
        dummy_process = ProcessFactory(name='process')

        ## Activities and Activity groups ##

        group_A = ActivityGroupFactory(name='A', code='A', keyflow=cls.keyflow)
        group_C = ActivityGroupFactory(name='C', code='C', keyflow=cls.keyflow)

        brewing_activity = ActivityFactory(
            name='Brewery',
            nace='A-0000', activitygroup=group_A)
        household_activity = ActivityFactory(
            name='Household',
            nace='A-0001', activitygroup=group_A)
        digester_activity = ActivityFactory(
            name='Digester',
            nace='A-0002', activitygroup=group_A)
        supermarket_activity = ActivityFactory(
            name='Supermarket',
            nace='A-0003', activitygroup=group_A)
        farming_activity = ActivityFactory(
            name='Farming',
            nace='C-0000', activitygroup=group_C)
        inciterator_activity = ActivityFactory(
            name='Incineration',
            nace='C-0001', activitygroup=group_C)

        ## Actors ##

        # random households
        for i in range(100):
            ActorFactory(name='household{}'.format(i),
                         activity=household_activity)
        # random supermarkets
        for i in range(10):
            ActorFactory(name='supermarket{}'.format(i),
                         activity=supermarket_activity)
        # random farms
        for i in range(2):
            ActorFactory(name='farm{}'.format(i),
                         activity=farming_activity)

        cls.brewery_1 = ActorFactory(name='brewery_1',
                                     activity=brewing_activity)
        cls.brewery_2 = ActorFactory(name='brewery_2',
                                     activity=brewing_activity)
        digester = ActorFactory(name='digester Amsterdam',
                                activity=digester_activity)
        incinerator = ActorFactory(name='incinerator Amsterdam',
                                activity=inciterator_activity)

        ## status quo flows ##
        households = Actor.objects.filter(activity=household_activity)
        farms = Actor.objects.filter(activity=farming_activity)
        breweries = Actor.objects.filter(activity=brewing_activity)
        supermarkets = Actor.objects.filter(activity=supermarket_activity)

        input_digester = 1000 / len(households)
        input_incinerator_bread = 500 / len(households)
        input_incinerator_other = 1500 / len(households)
        input_brewery_barley = 900 / len(farms)
        input_supermarket_beer = 4000 / (len(supermarkets) * len(breweries))

        # B: or whats with the FractionFlows?
        for i, household in enumerate(households):
            FractionFlowFactory(origin=household,
                                destination=digester,
                                material=bread,
                                amount=input_digester,
                                keyflow=cls.keyflow)
        for i, household in enumerate(households):
            FractionFlowFactory(origin=household,
                                destination=incinerator,
                                material=bread,
                                amount=input_incinerator_bread,
                                keyflow=cls.keyflow)
            FractionFlowFactory(origin=household,
                                destination=incinerator,
                                material=other_waste,
                                amount=input_incinerator_other,
                                keyflow=cls.keyflow)
        for i, farm in enumerate(farms):
            brewery = breweries[i]
            FractionFlowFactory(origin=farm,
                                destination=brewery,
                                material=barley,
                                amount=input_brewery_barley,
                                keyflow=cls.keyflow)
        for supermarket in supermarkets:
            for brewery in breweries:
                FractionFlowFactory(origin=brewery,
                                    destination=supermarket,
                                    material=beer,
                                    amount=input_supermarket_beer,
                                    keyflow=cls.keyflow)
        for brewery in breweries:
            FractionFlowFactory(origin=brewery,
                                destination=digester,
                                material=sludge,
                                amount=1000,
                                keyflow=cls.keyflow)


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
        material_names = [
            Mat('Plastic', is_waste=True),
            Mat('Crude Oil'),
            Mat('Petrol'),
            Mat('Milk'),
            Mat('Packaged Milk'),
            Mat('Packaged Cucumber'),
            Mat('Cucumber'),
            Mat('Human Waste', is_waste=True),
            Mat('Other Waste', is_waste=True)
        ]
        
        Frac = namedtuple('Fraction', ['composition', 'material', 'fraction'])
        Frac.__new__.__defaults__ = (None, None, 0.0)        
        fractions = [Frac('Packaged Milk', 'Milk', 0.25),
                     Frac('Packaged Milk', 'Plastic', 0.75),
                     Frac('Packaged Cucumber', 'Plastic', 0.15),
                     Frac('Packaged Cucumber', 'Cucumber', 0.85)
                     ]
        
        for mat in material_names:
            material = MaterialFactory(
                name=mat.name,
                keyflow=self.kic)
            self.materials[mat.name] = material
            Factory = WasteFactory if mat.is_waste else ProductFactory
            composition = Factory(name=mat.name)
            self.compositions[mat.name] = composition
            
        for frac in fractions:
            fraction = ProductFractionFactory(
                fraction=frac.fraction,
                material=self.materials[frac.material],
                composition=self.compositions[frac.composition],
                publication=self.pub,
            )
            self.fractions[frac.material] = fraction

    def create_actors(self):
        """Create the actors"""
        actor_names = {
            'oil_rig_den_haag': 'oil_rig',
            'oil_rig_rotterdam': 'oil_rig',
            'oil_refinery_rotterdam': 'oil_refinery',
            'shell_groningen_stock': 'stock',
            'production_utrecht': 'production',
            'production_leiden': 'production',
            'recycling_wageningen': 'recycling',
            'recycling_wageningen_stock': 'stock',
            'ah_den_haag_1': 'consumption',
            'ah_den_haag_2': 'consumption',
            'ah_den_haag_3': 'consumption',
            'packaging_leiden': 'packaging',
            'packaging_utrecht': 'packaging',
            'cucumber_farm_naaldwijk_1': 'farming',
            'cucumber_farm_naaldwijk_2': 'farming',
            'milk_farm_friesland_1': 'farming',
            'milk_farm_friesland_2': 'farming',
            'incinerator_eindhoven': 'waste_treatment',
            'paper_waste_collector_enschede': 'waste_treatment',
            'organic_waste_collector_nijmegen': 'waste_treatment'
        }
        self.actors = {}
        for actor_name, activity_name in actor_names.items():
            self.actors[actor_name] = ActorFactory(
                name=actor_name,
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
            Flow('oil_rig_den_haag', 'oil_refinery_rotterdam', 'Crude Oil', 5),
            Flow('oil_rig_rotterdam', 'oil_refinery_rotterdam', 'Crude Oil', 15),
            Flow('oil_refinery_rotterdam', 'shell_groningen_stock', 'Petrol', 1600),
            Flow('oil_refinery_rotterdam', 'production_utrecht', 'Plastic', 100),
            Flow('oil_refinery_rotterdam', 'production_leiden', 'Plastic', 300),
            Flow('production_utrecht', 'packaging_utrecht', 'Plastic', 125),
            Flow('production_leiden', 'packaging_leiden', 'Plastic', 375),
            Flow('cucumber_farm_naaldwijk_1', 'packaging_utrecht', 'Cucumber', 1500),
            Flow('cucumber_farm_naaldwijk_2', 'packaging_utrecht', 'Cucumber', 1500),
            Flow('milk_farm_friesland_1', 'packaging_leiden', 'Milk', 2500),
            Flow('milk_farm_friesland_2', 'packaging_leiden', 'Milk', 4000),
            Flow('packaging_utrecht', 'ah_den_haag_1', 'Packaged Cucumber', 1000),
            Flow('packaging_utrecht', 'ah_den_haag_2', 'Packaged Cucumber', 1500),
            Flow('packaging_utrecht', 'ah_den_haag_3', 'Packaged Cucumber', 500),
            Flow('packaging_leiden', 'ah_den_haag_1', 'Packaged Milk', 2500),
            Flow('packaging_leiden', 'ah_den_haag_2', 'Packaged Milk', 1000),
            Flow('packaging_leiden', 'ah_den_haag_3', 'Packaged Milk', 3000),
            Flow('ah_den_haag_1', 'incinerator_eindhoven', 'Other Waste', 100),
            Flow('ah_den_haag_2', 'incinerator_eindhoven', 'Other Waste', 100),
            Flow('ah_den_haag_3', 'incinerator_eindhoven', 'Other Waste', 100),
            Flow('ah_den_haag_1', 'paper_waste_collector_enschede', 'Other Waste', 800),
            Flow('ah_den_haag_2', 'paper_waste_collector_enschede', 'Other Waste', 400),
            Flow('ah_den_haag_3', 'paper_waste_collector_enschede', 'Other Waste', 800),
            Flow('ah_den_haag_1', 'organic_waste_collector_nijmegen', 'Human Waste', 2500),
            Flow('ah_den_haag_2', 'organic_waste_collector_nijmegen', 'Human Waste', 2500),
            Flow('ah_den_haag_3', 'organic_waste_collector_nijmegen', 'Human Waste', 2500),
            Flow('ah_den_haag_1', 'recycling_wageningen', 'Plastic', 25),
            Flow('ah_den_haag_2', 'recycling_wageningen', 'Plastic', 75),
            Flow('ah_den_haag_3', 'recycling_wageningen', 'Plastic', 100),
            Flow('recycling_wageningen', 'production_utrecht', 'Plastic', 50),
            Flow('recycling_wageningen', 'production_leiden', 'Plastic', 50),
            Flow('recycling_wageningen', 'recycling_wageningen_stock', 'Other Waste', 100)
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
    def create_solutions(self):
        """Create the solutions"""
        Solution = namedtuple('Solution', ['affected_flows',
                                   'solution_flows',
                                   'solution',
                                   'flow_to_remove',
                                   'target_vertex',
                                   'ratio'])
        Solution.__new__.__defaults__ = (None, None, 0.0, None, None, 0.0)
        self.solutions = [
            Solution([(3, "Plastic"),(5, "Plastic"),(26, "Plastic"),(27, "Plastic"),(28, "Plastic"),(29, "Plastic")],
                     [(11, "Plastic"),(12, "Plastic"),(13, "Plastic")],2),
            Solution([(1, "Crude Oil"), (2, "Crude Oil")],[],3),
            Solution([],[],4)
        ]
        

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
