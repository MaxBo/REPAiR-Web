define(["backbone", "models/stakeholder", "app-config"],

    function(Backbone, Stakeholder, config) {

        /**
         *
         * @author Balázs Dukai
         * @name module:collections/Stakeholders
         * @augments Backbone.Collection
         */
        var Stakeholders = Backbone.Collection.extend(
            /** @lends module:collections/Stakeholders.prototype */
            {
                /**
                 * generates an url to the api resource list based on the ids given in constructor
                 *
                 * @returns {string} the url string
                 */
                url: function() {
                    // get all stakeholders in stakeholderCategory
                    return config.api.stakeholders.format(this.caseStudyId,
                        this.stakeholderCategoryId);
                },

                model: Stakeholder,

                /**
                 * collection of module:models/Actor
                 *
                 * @param {Array.<Object>} [attrs=null]             list objects representing the fields of each model and their values, will be set if passed
                 * @param {Object} options
                 * @param {string} options.caseStudyId              id of the casestudy the actors belong to
                 * @param {string} options.stakeholderCategoryId    id of the stakeholderCategory the stakeholder belongs to
                 *
                 * @constructs
                 * @see http://backbonejs.org/#Collection
                 */
                initialize: function(attrs, options) {
                    this.caseStudyId = options.caseStudyId;
                    this.stakeholderCategoryId = options.stakeholderCategoryId;
                }
            });

        return Stakeholders;
    }
);
