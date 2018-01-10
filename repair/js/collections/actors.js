define(["backbone", "models/actor", "app-config"],

  function(Backbone, Actor, config) {
  
    var Actors = Backbone.Collection.extend({
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