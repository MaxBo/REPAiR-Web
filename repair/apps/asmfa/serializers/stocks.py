
from repair.apps.asmfa.models import (Stock,
                                      GroupStock,
                                      ActivityStock,
                                      ActorStock,
                                      )

from repair.apps.login.serializers import (NestedHyperlinkedModelSerializer,
                                           IDRelatedField)


from .keyflows import (KeyflowInCasestudyField,
                       KeyflowInCasestudyDetailCreateMixin)


class StockSerializer(KeyflowInCasestudyDetailCreateMixin,
                      NestedHyperlinkedModelSerializer):
    keyflow = KeyflowInCasestudyField(view_name='keyflowincasestudy-detail',
                                      read_only=True)
    product = IDRelatedField()
    publication = IDRelatedField()

    parent_lookup_kwargs = {
        'casestudy_pk': 'keyflow__casestudy__id',
        'keyflow_pk': 'keyflow__id',
    }

    class Meta:
        model = Stock
        fields = ('url', 'id', 'origin', 'amount',
                  'keyflow', 'year', 'product',
                  'publication', 
                  )


class GroupStockSerializer(StockSerializer):
    origin = IDRelatedField()

    class Meta(StockSerializer.Meta):
        model = GroupStock


class ActivityStockSerializer(StockSerializer):
    origin = IDRelatedField()

    class Meta(StockSerializer.Meta):
        model = ActivityStock


class ActorStockSerializer(StockSerializer):
    origin = IDRelatedField()

    class Meta(StockSerializer.Meta):
        model = ActorStock
