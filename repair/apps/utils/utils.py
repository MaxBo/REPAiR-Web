from repair.apps.asmfa.models import Material
from django.db.models import AutoField

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