define(["backbone", "app-config"],

  function(Backbone, config) {

   /**
    *
    * @author Christoph Franke
    * @name module:models/Actor
    * @augments Backbone.Model
    */
    var Actor = Backbone.Model.extend(
      /** @lends module:models/Actor.prototype */
      {
      idAttribute: "id",
      tag: 'actor',
      /**
       * generates an url to the api resource based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      urlRoot: function(){
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
     * model for fetching/putting an actor
     *
     * @param {Object} [attributes=null]          fields of the model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId        id of the casestudy the actor belongs to
     * @param {string} options.keyflowId          id of the keyflow the actor belongs to
     * @param {string} options.activityGroupCode  id of the activitygroup the actor belongs to
     * @param {string} options.activityId         id of the activity the actor belongs to
     *
     * @constructs
     * @see http://backbonejs.org/#Model
     */
      initialize: function (attributes, options) {
        this.caseStudyId = options.caseStudyId;
        this.activityId = options.activityId;
        this.activityGroupCode = options.activityGroupCode;
        this.keyflowId = options.keyflowId;
        // out of a sudden backbone didn't set the urlRoot correctly, if instantiated via actors-collection
        // workaround: take url passed by collection as urlRoot
        //if (options.url)
          //this.urlRoot = options.url;
      },

    });
    return Actor;
  }
);