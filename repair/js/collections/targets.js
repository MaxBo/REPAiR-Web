define(["backbone", "models/target", "app-config"],

    function(Backbone, Target, config) {

        /**
         * @author Balázs Dukai
         * @name module:collections/Targets
         * @augments Backbone.Collection
         */
        var Targets = Backbone.Collection.extend(
            /** @lends module:collections/Targets.prototype */
            {
                /**
                 * generates an url to the api resource list based on the ids given in constructor
                 *
                 * @returns {string} the url string
                 */
                url: function() {
                    return config.api.targets.format(this.caseStudyId);
                },

                model: Target,

                /**
                 * collection for fetching/putting categories of stakeholder definitions
                 *
                 * @param {Array.<Object>} [attrs=null]   list objects representing the fields of each model and their values, will be set if passed
                 * @param {Object} options
                 * @param {string} options.caseStudyId  id of the casestudy the categories belong to
                 *
                 * @constructs
                 * @see http://backbonejs.org/#Collection
                 */
                initialize: function(attrs, options) {
                    this.caseStudyId = options.caseStudyId;
                }
            })
        return Targets;
    }
);
