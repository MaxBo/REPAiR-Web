import logging

from django.db import models, router
from django.core.exceptions import (ValidationError,
                                    AppRegistryNotReady)
from django.db.utils import OperationalError, IntegrityError
from django.db.models.deletion import Collector

logger = logging.getLogger(__name__)


class GDSEModelMixin:

    @property
    def bulk_upload(self):
        return None

    def delete(self, using=None, keep_parents=False, use_protection=False):
        """
        delete the object

        Parameters:
        using: str, optional
        keep_parents: bool, optional(default=False)

        use_protection: bool, optional(default=False)
            if True, raise a ProtectedError
            when trying to delete related objects if on_delete=PROTECT_CASCADE
            if False, delete objects cascaded
        """
        using = using or router.db_for_write(self.__class__, instance=self)
        assert self.pk is not None, (
            "%s object can't be deleted because its %s attribute is set to None." %
            (self._meta.object_name, self._meta.pk.attname)
        )

        collector = Collector(using=using)
        collector.use_protection = use_protection
        collector.collect([self], keep_parents=keep_parents)
        return collector.delete()


class GDSEModel(GDSEModelMixin, models.Model):
    """Base class for the GDSE Models"""

    class Meta:
        abstract = True
        default_permissions = ('add', 'change', 'delete', 'view')

    def __str__(self):
        try:
            return self.name or ''
        except Exception:
            return ''

    def __lt__(self, other):
        return self.id < other.id

    def __gt__(self, other):
        return self.id > other.id


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
