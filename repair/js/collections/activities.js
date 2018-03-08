define(["backbone", "models/activity", "app-config"],

  function(Backbone, Activity, config) {
  
   /**
    *
    * @author Christoph Franke
    * @name module:collections/Activities
    * @augments Backbone.Collection
    */
    var Activities = Backbone.Collection.extend(
      /** @lends module:collections/Activities.prototype */
      {
      /**
       * generates an url to the api resource list based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      url: function(){
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
     * collection of module:models/Activity
     *
     * @param {Array.<Object>} [attrs=null]         list objects representing the fields of each model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId        id of the casestudy the activities belong to
     * @param {string} options.activityGroupCode  id of the activitygroup the activities belong to
     * @param {string} options.keyflowId          id of the keyflow the activities belong to
     *
     * @constructs
     * @see http://backbonejs.org/#Collection
     */
      initialize: function (attrs, options) {
        this.caseStudyId = options.caseStudyId;
        this.activityGroupCode = options.activityGroupCode;
        this.keyflowId = options.keyflowId;
      },
      
      /**
       * filter the collection to find models belonging to an activitygroup with the given id
       *
       * @param {string} groupId id of the group
       *
       * @returns {Array.<module:models/Activity>} list of all activities belonging to the group
       */
      filterGroup: function (groupId) {
          var filtered = this.filter(function (activity) {
              return activity.get("activitygroup") == groupId;
          });
          return filtered;
      },
      
      model: Activity
    });
    
    return Activities;
  }
);