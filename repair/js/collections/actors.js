define(["backbone", "models/actor", "app-config"],

  function(Backbone, Actor, config) {
  
   /**
    *
    * @author Christoph Franke
    * @name module:collections/Actors
    * @augments Backbone.Collection
    */
    var Actors = Backbone.Collection.extend(
      /** @lends module:collections/Actors.prototype */
      {
      /**
       * generates an url to the api resource list based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      url: function(){
        // if an activity is given, take the route that retrieves all actors 
        // of the activity
        if (this.activityId != null)
          return config.api.actorsInGroup.format(
            this.caseStudyId, this.keyflowId, this.activityGroupCode, this.activityId);
        // if no activity is given, get all activities in the casestudy
        else
          return config.api.actors.format(this.caseStudyId, this.keyflowId);
      },
      
      /**
       * filter the collection to find models belonging to an activity with the given id
       *
       * @param {string} activityId   id of the activity
       *
       * @returns {Array.<module:models/Actor>} list of all actors belonging to the activity
       */
      filterActivity: function (activityId) {
          var filtered = this.filter(function (actor) {
              return actor.get("activity") == activityId;
          });
          return filtered;
      },
      
      /**
       * filter the collection to find models belonging to an activitygroup with the given id
       *
       * @param {string} groupId   id of the activitygroup
       *
       * @returns {Array.<module:models/Actor>} list of all actors belonging to the activitygroup
       */
      filterGroup: function (groupId) {
          var filtered = this.filter(function (actor) {
              return actor.get("activitygroup") == groupId;
          });
          return filtered;
      },
   
    /**
     * collection of module:models/Actor
     *
     * @param {Array.<Object>} [attrs=null]         list objects representing the fields of each model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId        id of the casestudy the actors belong to
     * @param {string} options.activityId         id of the activity the actors belong to
     * @param {string} options.activityGroupCode  id of the activitygroup the actors belong to
     * @param {string} options.keyflowId          id of the keyflow the actors belong to
     *
     * @constructs
     * @see http://backbonejs.org/#Collection
     */
      initialize: function (attrs, options) {
        this.caseStudyId = options.caseStudyId;
        this.activityId = options.activityId;
        this.activityGroupCode = options.activityGroupCode;
        this.keyflowId = options.keyflowId;
      },
      model: Actor
    });
    
    return Actors;
  }
);