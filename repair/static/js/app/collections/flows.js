define(["backbone", "app-config"],

  function(Backbone, config) {
  
    var Activities = Backbone.Collection.extend({
      url: function(){
        var url = (this.type == 'activity') ? config.api.activityToActivity:
                  (this.type == 'actor') ? config.api.actorToActor:
                  config.api.groupToGroup;
        return url.format(this.caseStudyId, this.keyflowId);
      },
      
      initialize: function (models, options) {
        this.caseStudyId = options.caseStudyId;
        this.keyflowId = options.keyflowId;
        this.type = options.type;
      }
    });
    
    return Activities;
  }
);