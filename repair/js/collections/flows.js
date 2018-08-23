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
            * filters flows that link given origins and destinations
            *
            * @param {Array.Number} origins      ids of origins
            * @param {Array.Number} destinations ids of destinations
            *
            * @returns {GDSECollection} filtered flows
            */
            filterByNodes: function (origins, destinations) {
                var filtered = this.filterBy({
                    origin: origins,
                    destination: destinations
                })
                return filtered;
            },

            /**
            * aggregate given flows
            *
            * @param {Array.Number} ids  ids of flows to aggregate
            *
            * @returns {GDSEModel} aggregated flow
            */
            aggregate: function (ids) {
                return null;
            }
        });

        return Flows;
    }
);
