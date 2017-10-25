define(["backbone", "app/models/activity"],

  function(Backbone, Activity) {
  
    var Activities = Backbone.Collection.extend({
      url: function(){
        if (this.activityGroupCode != null)
          return config.api.activitiesInGroup.format(this.caseStudyId, 
                                              this.activityGroupCode);
        else
          return config.api.activities.format(this.caseStudyId);
      },
      
      initialize: function (options) {
        this.caseStudyID = options.caseStudyID;
        this.activityGroupCode = options.activityGroupCode;
      },
      model: Activity
    });
    
    return Activities;
  }
);