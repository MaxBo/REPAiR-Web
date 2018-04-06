define(["backbone", "app-config"],

    function(Backbone, config) {

        /**
         *
         * @author Balázs Dukai
         * @name module:models/Aim
         * @augments Backbone.Model
         */
        var Aim = Backbone.Model.extend(
            /** @lends module:models/Aim.prototype */
            {
                idAttribute: "id",

                /**
                 * generates an url to the api resource based on the ids given in constructor
                 *
                 * @returns {string} the url string
                 */
                urlRoot: function() {
                    return config.api.aims.format(this.caseStudyId);
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
        return Aim;
    }
);
