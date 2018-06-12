import os
from django.db.models import CASCADE, PROTECT


def PROTECT_CASCADE(collector, field, sub_objs, using):
    """
    Protect the deletion of a foreign key, if the environment variable
    `PROTECT_FOREIGN_KEY=True` is set.
    Otherwise use CASCADE
    """
    if os.environ.get('PROTECT_FOREIGN_KEY') == 'True':
        PROTECT(collector, field, sub_objs, using)
    else:
        CASCADE(collector, field, sub_objs, using)
