define(["backbone", "app-config"],

    function(Backbone, config) {

        /**
         *
         * @author Balázs Dukai
         * @name module:models/Challenge
         * @augments Backbone.Model
         */
        var Challenge = Backbone.Model.extend(
            /** @lends module:models/Challenge.prototype */
            {
                idAttribute: "id",

                /**
                 * generates an url to the api resource based on the ids given in constructor
                 *
                 * @returns {string} the url string
                 */
                urlRoot: function() {
                    return config.api.challenges.format(this.caseStudyId);
                },

                /**
                 * model for fetching/putting a category of stakeholder definitions
                 *
                 * @param {Object} [attributes=null]       fields of the model and their values, will be set if passed
                 * @param {Object} options
                 * @param {string} options.caseStudyId     id of the casestudy the category belongs to
                 *
                 * @constructs
                 * @see http://backbonejs.org/#Model
                 */
                initialize: function(attributes, options) {
                    this.caseStudyId = options.caseStudyId;
                }

            });
        return Challenge;
    }
);
