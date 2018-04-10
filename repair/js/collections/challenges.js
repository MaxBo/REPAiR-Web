define(["backbone", "models/challenge", "app-config"],

    function(Backbone, Challenge, config) {

        /**
         * @author Balázs Dukai
         * @name module:collections/Challenges
         * @augments Backbone.Collection
         */
        var Challenges = Backbone.Collection.extend(
            /** @lends module:collections/Challenges.prototype */
            {
                /**
                 * generates an url to the api resource list based on the ids given in constructor
                 *
                 * @returns {string} the url string
                 */
                url: function() {
                    return config.api.challenges.format(this.caseStudyId);
                },

                model: Challenge,

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
        return Challenges;
    }
);
