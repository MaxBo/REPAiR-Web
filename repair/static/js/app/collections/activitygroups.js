define(["backbone", "app/models/activitygroup", "app-config"],

  function(Backbone, ActivityGroup, config) {
  
    var ActivityGroups = Backbone.Collection.extend({
      url: function(){
        return config.api.activitygroups.format(this.caseStudyId);
      },
      
      initialize: function (models, options) {
        this.caseStudyId = options.caseStudyId;
      },
      model: ActivityGroup
    });
    
    return ActivityGroups;
  }
);