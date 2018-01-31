
from repair.apps.asmfa.models import (Stock,
                                      GroupStock,
                                      ActivityStock,
                                      ActorStock,
                                      )

from repair.apps.login.serializers import (NestedHyperlinkedModelSerializer,
                                           IDRelatedField)


from repair.apps.asmfa.serializers.keyflows import (
    KeyflowInCasestudyField, KeyflowInCasestudyDetailCreateMixin,
    ProductFractionSerializer, CompositionSerializer)


class StockSerializer(KeyflowInCasestudyDetailCreateMixin,
                      NestedHyperlinkedModelSerializer):
    keyflow = KeyflowInCasestudyField(view_name='keyflowincasestudy-detail',
                                      read_only=True)
    composition = CompositionSerializer()
    publication = IDRelatedField(allow_null=True, required=False)

    parent_lookup_kwargs = {
        'casestudy_pk': 'keyflow__casestudy__id',
        'keyflow_pk': 'keyflow__id',
    }

    class Meta:
        model = Stock
        fields = ('url', 'id', 'origin', 'amount',
                  'keyflow', 'year', 'composition',
                  'publication', 'waste' 
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
