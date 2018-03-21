define(["backbone", "app-config"],

    function(Backbone, config) {

        /**
         *
         * @author Balázs Dukai
         * @name module:models/Stakeholder
         * @augments Backbone.Model
         */
        var Stakeholder = Backbone.Model.extend(
            /** @lends module:models/Stakeholder.prototype */
            {
                idAttribute: "id",
                tag: 'stakeholder',
                /**
                 * generates an url to the api resource based on the ids given in constructor
                 *
                 * @returns {string} the url string
                 */
                urlRoot: function() {
                    // get all stakeholders in stakeholderCategory
                    return config.api.stakeholders.format(this.caseStudyId,
                        this.stakeholderCategoryId);
                },

                /**
                 * model for fetching/putting a stakeholder
                 *
                 * @param {Object} [attributes=null]                fields of the model and their values, will be set if passed
                 * @param {Object} options
                 * @param {string} options.caseStudyId              id of the casestudy the stakeholder belongs to
                 * @param {string} options.stakeholderCategoryId    id of the stakeholderCategory the stakeholder belongs to
                 *
                 * @constructs
                 * @see http://backbonejs.org/#Model
                 */
                initialize: function(attributes, options) {
                    this.caseStudyId = options.caseStudyId;
                    this.stakeholderCategoryId = options.stakeholderCategoryId;
                }
            });
        return Stakeholder;
    }
);
