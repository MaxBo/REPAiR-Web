define(["backbone", "app-config"],

  function(Backbone, config) {

   /**
    *
    * @author Christoph Franke
    * @name module:models/Activity
    * @augments Backbone.Model
    */
    var Activity = Backbone.Model.extend(
      /** @lends module:models/Activity.prototype */
      {
      idAttribute: "id",
      tag: "activity",
      
      /**
       * generates an url to the api resource based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      urlRoot: function(){
        // if a group is given, take the route that retrieves all activities 
        // of the group
        if (this.activityGroupCode != null)
          return config.api.activitiesInGroup.format(this.caseStudyId, 
                                                     this.keyflowId,
                                                     this.activityGroupCode);
        // if no group is given, get all activities in the casestudy
        else
          return config.api.activities.format(this.caseStudyId, this.keyflowId);
      },

    /**
     * model for fetching/putting an activity
     *
     * @param {Object} [attributes=null]          fields of the model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId        id of the casestudy the activity belongs to
     * @param {string} options.activityGroupCode  id of the activitygroup the activity belongs to
     * @param {string} options.keyflowId          id of the keyflow the activity belongs to
     *
     * @constructs
     * @see http://backbonejs.org/#Model
     */
      initialize: function (attributes, options) {
        this.caseStudyId = options.caseStudyId;
        this.activityGroupCode = options.activityGroupCode;
        this.keyflowId = options.keyflowId;
      },

    });
    return Activity;
  }
);