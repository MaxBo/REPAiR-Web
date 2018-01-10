define(["backbone", "models/activitygroup", "app-config"],

  function(Backbone, ActivityGroup, config) {
  
    var ActivityGroups = Backbone.Collection.extend({
      url: function(){
        return config.api.activitygroups.format(this.caseStudyId, this.keyflowId);
      },
      
      initialize: function (attrs, options) {
        this.caseStudyId = options.caseStudyId;
        this.keyflowId = options.keyflowId;
      },
      model: ActivityGroup
    });
    
    return ActivityGroups;
  }
);