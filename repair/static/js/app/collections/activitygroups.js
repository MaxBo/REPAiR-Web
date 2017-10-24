define(["backbone", "app/models/activitygroup"],

  function(Backbone, ActivityGroup) {
  
    var ActivityGroups = Backbone.Collection.extend({
      url: function(){
        return config.api.activitygroups.format(this.caseStudyID);
      },
      
      initialize: function (options) {
        this.caseStudyID = options.caseStudyID;
      },
      model: ActivityGroup
    });
    
    return ActivityGroups;
  }
);