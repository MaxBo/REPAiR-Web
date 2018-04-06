define(["backbone-pageable",  "models/actor", "app-config"],

  function(PageableCollection, Actor, config) {
  
   /**
    *
    * @author Christoph Franke
    * @name module:collections/Actors
    * @augments Backbone.PageableCollection
    *
    * @see https://github.com/backbone-paginator/backbone.paginator
    */
    var Actors = PageableCollection.extend(
      /** @lends module:collections/Actors.prototype */
      {
      /**
       * generates an url to the api resource list based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      url: function(){
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
      
      queryParams: {
        pageSize: "page_size"
      },
      
      parseRecords: function (response) {
        return response.results;
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
        this.keyflowId = options.keyflowId;
      },
      model: Actor
    });
    
    return Actors;
  }
);