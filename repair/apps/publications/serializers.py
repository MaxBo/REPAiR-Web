import datetime
from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _
from django.core.validators import URLValidator
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import ValidationError


from repair.apps.login.models import CaseStudy
from repair.apps.publications.models import (PublicationInCasestudy,
                                             Publication,
                                             PublicationType,
                                            )

from repair.apps.login.serializers import (NestedHyperlinkedModelSerializer,
                                           InCasestudySerializerMixin,)


class PublicationInCasestudySerializer(InCasestudySerializerMixin,
                                       NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}

    publication_id = serializers.CharField(source='publication.id',
                                           required=False)
    type = serializers.CharField(source='publication.type', required=False,
                                 default='Article')
    citekey = serializers.CharField(source='publication.citekey',
                                 allow_blank=True, required=False)
    title = serializers.CharField(source='publication.title',
                                 allow_blank=True, required=False)
    authors = serializers.CharField(source='publication.authors',
                                 allow_blank=True, required=False)
    year = serializers.IntegerField(source='publication.year', required=False,
                                    default=datetime.datetime.now().year)
    doi = serializers.CharField(source='publication.doi',
                                 allow_blank=True, required=False)
    casestudy = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = PublicationInCasestudy
        fields = ('url',
                  'id',
                  'publication_id',
                  'casestudy',
                  'type',
                  'citekey',
                  'title',
                  'authors',
                  'year',
                  'doi',
                  'casestudy',
                  )

    def create(self, validated_data):
        """Create a new keyflow in casestury"""
        casestudy_id = validated_data.pop('casestudy_id', None)
        if casestudy_id:
            casestudy = CaseStudy.objects.get(pk=casestudy_id)
        else:
            casestudy = self.get_casestudy()
        publication_data = validated_data.pop('publication', {})
        publication_type = self.get_publication_type(publication_data)
        year = publication_data.pop('year', self.fields['year'].default)
        publication, created = Publication.objects.get_or_create(
            type=publication_type, year=year, **publication_data)
        obj = self.Meta.model.objects.create(
            casestudy=casestudy,
            publication=publication,
            **validated_data)
        return obj

    def get_publication_type(self, publication_data):
        publication_type = publication_data.pop('type',
                                                self.fields['type'].default)
        publication_type, created = PublicationType.objects.get_or_create(
            title=publication_type)
        return publication_type

    def update(self, obj, validated_data):
        publication = Publication.objects.get(publicationincasestudy=obj.pk)
        publication_data = validated_data.pop('publication', {})
        publication_type = self.get_publication_type(publication_data)
        if publication_type:
            publication.type = publication_type
        for attr, value in publication_data.items():
            setattr(publication, attr, value)
        publication.save()
        return super().update(obj, validated_data)
