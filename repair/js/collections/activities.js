define(["backbone", "models/activity", "app-config"],

  function(Backbone, Activity, config) {
  
    var Activities = Backbone.Collection.extend({
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
      
      initialize: function (attrs, options) {
        this.caseStudyId = options.caseStudyId;
        this.activityGroupCode = options.activityGroupCode;
        this.keyflowId = options.keyflowId;
      },
      model: Activity
    });
    
    return Activities;
  }
);