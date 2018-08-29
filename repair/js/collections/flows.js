define(["backbone", "collections/gdsecollection"],
    function(Backbone, GDSECollection) {

        /**
        *
        * @author Christoph Franke
        * @name module:collections/Flows
        * @augments Backbone.Collection
        */
        var Flows = GDSECollection.extend(
        /** @lends module:collections/Locations.prototype */
        {

            /**
            * aggregate flows (with ids if given)
            *
            * @param {Array.Number=} ids  optional ids of flows to aggregate
            *
            * @returns {GDSEModel} aggregated flow
            */
            aggregate: function (ids) {
                var flows = (ids) ? this.filterBy({id: ids}) : this,
                    totalAmount = 0,
                    idsDone = [],
                    materialAmounts = {};

                this.forEach(function(flow){
                    var comp = flow.get('composition'),
                        amount = flow.get('amount');
                    if(!comp || !comp.fractions) return;
                    totalAmount += amount;
                    comp.fractions.forEach(function(fraction){
                        var mat = fraction.material;
                        if(!materialAmounts[mat]) materialAmounts[mat] = 0;
                        materialAmounts[mat] += amount * fraction.fraction;
                    })
                    idsDone.push(flow.id);
                })

                var fractions = [];
                for (var matId in materialAmounts){
                    fractions.push({
                        material: matId,
                        fraction: materialAmounts[matId] / totalAmount
                    })
                }

                aggregated = new this.model({
                    amount: totalAmount,
                    id: ['agg'].concat(idsDone).join('-'),
                    name: 'aggregated',
                    composition: {
                        id: null,
                        fractions: fractions,
                        name: 'aggregated'
                    }
                })
                return aggregated;
            }
        });

        return Flows;
    }
);
