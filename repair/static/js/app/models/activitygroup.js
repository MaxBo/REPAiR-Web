define(["backbone", "app-config"],

  function(Backbone, config) {

   /**
    *
    * @author Christoph Franke
    * @name module:models/ActivityGroup
    * @augments Backbone.Model
    */
    var ActivityGroup = Backbone.Model.extend(
      /** @lends module:models/ActivityGroup.prototype */
      {
      idAttribute: "id",
      tag: "activitygroup",
      /**
       * generates an url to the api resource based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      urlRoot: function(){
        return config.api.activitygroups.format(this.caseStudyId, this.keyflowId);
      },

    /**
     * model for fetching/putting an activitygroup
     *
     * @param {Object} [attributes=null]          fields of the model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId        id of the casestudy the activitygroup belongs to
     * @param {string} options.keyflowId          id of the keyflow the activitygroup belongs to
     *
     * @constructs
     * @see http://backbonejs.org/#Model
     */
      initialize: function (attributes, options) {
        this.caseStudyId = options.caseStudyId;
        this.keyflowId = options.keyflowId;
      },

    });
    return ActivityGroup;
  }
);