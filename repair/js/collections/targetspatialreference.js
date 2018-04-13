define(["backbone", "app-config"],

    function(Backbone, config) {

        /**
         * @author Balázs Dukai
         * @name module:collections/TargetSpatialReference
         * @augments Backbone.Collection
         */
        var TargetSpatialReference = Backbone.Collection.extend(
            /** @lends module:collections/TargetSpatialReference.prototype */
            {
                /**
                 * generates an url to the api resource list based on the ids given in constructor
                 *
                 * @returns {string} the url string
                 */
                url: function() {
                    return config.api.targetspatialreference
                },

                /**
                 * collection for fetching/putting categories of stakeholder definitions
                 *
                 * @param {Array.<Object>} [attrs=null]   list objects representing the fields of each model and their values, will be set if passed
                 * @param {Object} options
                 *
                 * @constructs
                 * @see http://backbonejs.org/#Collection
                 */
                initialize: function(attrs, options) {
                }
            })
        return TargetSpatialReference;
    }
);
