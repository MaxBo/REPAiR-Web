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

    def __str__(self):
        return self.name or ''


class GDSEUniqueNameModel(GDSEModel):
    """Base class for the GDSE Models"""
    _unique_field = 'name'

    class Meta:
        abstract = True

    def validate_unique(self, exclude=None):
        super().validate_unique(exclude=exclude)

        qs = self.__class__._default_manager.filter(
            **{self._unique_field: getattr(self, self._unique_field)}
        )

        if qs.exists():
            for row in qs:
                if row.casestudy == self.casestudy:
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
