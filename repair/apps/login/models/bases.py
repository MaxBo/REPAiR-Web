import logging

from django.db import models
from django.core.exceptions import (ValidationError,
                                    AppRegistryNotReady)
from django.db.utils import OperationalError, IntegrityError

logger = logging.getLogger(__name__)


class GDSEModel(models.Model):
    """Base class for the GDSE Models"""

    class Meta:
        abstract = True
        default_permissions = ('add', 'change', 'delete', 'view')


    def __str__(self):
        try:
            return self.name or ''
        except Exception:
            return ''

    @property
    def _upload_file(self):
        return None


class GDSEUniqueNameModel(GDSEModel):
    """Base class for the GDSE Models"""
    _unique_field = 'name'

    class Meta(GDSEModel.Meta):
        abstract = True

    def validate_unique(self, exclude=None):
        super().validate_unique(exclude=exclude)

        qs = self.__class__._default_manager.filter(
            **{self._unique_field: getattr(self, self._unique_field)}
        )

        if qs.exists():
            for row in qs:
                # if object's unique field already exists
                # for other object in the same casestudy
                if (row.casestudy == self.casestudy) and (row.pk != self.pk):
                    msg = '{cl} {n} already exists in casestudy {c}'
                    raise ValidationError(msg.format(
                        cl=self.__class__.__name__,
                        n=getattr(self, self._unique_field),
                        c=self.casestudy,))

    def save(self, *args, **kwargs):
        """Call :meth:`full_clean` before saving."""
        if self.pk is None:
            self.full_clean()
        super().save(*args, **kwargs)
