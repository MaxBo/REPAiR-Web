from repair.apps.asmfa.models import Material
from django.db.models.functions import Coalesce
from django.db.models import (AutoField, Q, F, Case, When, FilteredRelation)
from repair.apps.asmfa.models import FractionFlow

def copy_django_model(obj):
    initial = dict([(f.name, getattr(obj, f.name))
                    for f in obj._meta.fields
                    if not isinstance(f, AutoField) and\
                       not f in obj._meta.parents.values()])
    return obj.__class__(**initial)

def descend_materials(materials):
    """return list of material ids of given materials and all of their
    descendants
    """
    mats = []
    all_materials = Material.objects.values_list('id', 'parent__id')
    mat_dict = {}

    # might seem strange to build a dict with all materials and it's
    # children, but this is in fact 1000 times faster than
    # doing this in iteration over given material queryset
    for mat_id, parent_id in all_materials:
        if not parent_id:
            continue
        parent_entry = mat_dict.get(parent_id)
        if not parent_entry:
            parent_entry = []
            mat_dict[parent_id] = parent_entry
        parent_entry.append(mat_id)

    def get_descendants(mat_id):
        descendants = []
        children = mat_dict.get(mat_id, [])
        for child_id in children:
            descendants.append(child_id)
            descendants.extend(get_descendants(child_id))
        return descendants

    # use the dict to get all descending child materials
    for material in materials:
        # get the children of the given material
        mats.extend(get_descendants(material.id))
        # fractions have to contain children and the material itself
        mats.append(material.id)
    return mats


def get_annotated_fractionflows(keyflow_id, strategy_id=None):
    '''
    returns fraction flows in given keyflow

    annotates fraction flow queryset flows with values of fields
    of strategy fraction flows ('strategy_' as prefix to original field)

    strategy fraction flows override fields of fraction flow (prefix 'strategy_') if
    changed in strategy
    '''

    queryset = FractionFlow.objects
    if not strategy_id:
        queryset = queryset.filter(
            keyflow__id=keyflow_id,
            strategy__isnull=True).\
            annotate(
                strategy_amount=F('amount'),
                strategy_material=F('material'),
                strategy_material_name=F('material__name'),
                strategy_material_level=F('material__level'),
                strategy_waste=F('waste'),
                strategy_hazardous=F('hazardous'),
                strategy_process=F('process'),
                # just setting Value(0) doesn't seem to work
                strategy_delta=F('strategy_amount') - F('amount')
        )
    else:
        qs1 = queryset.filter(
            Q(keyflow__id=keyflow_id) &
            (Q(strategy__isnull=True) |
             Q(strategy_id=strategy_id))
        )
        qsfiltered = qs1.annotate(sf=FilteredRelation(
            'f_strategyfractionflow',
            condition=Q(f_strategyfractionflow__strategy=strategy_id)))
        queryset = qsfiltered.annotate(
            # strategy fraction flow overrides amounts
            strategy_amount=Coalesce('sf__amount', 'amount'),
            strategy_material=Coalesce('sf__material', 'material'),
            strategy_material_name=Coalesce(
                'sf__material__name', 'material__name'),
            strategy_material_level=Coalesce(
                'sf__material__level', 'material__level'),
            strategy_waste=Coalesce('sf__waste', 'waste'),
            strategy_hazardous=Coalesce('sf__hazardous', 'hazardous'),
            strategy_process=Coalesce('sf__process', 'process'),
            #strategy_delta=Case(When(strategy=strategy,
                                     #then=F('strategy_amount')),
                                #default=F('strategy_amount') - F('amount'))
        )

    return queryset.order_by('origin', 'destination')
