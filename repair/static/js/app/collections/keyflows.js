define(["backbone", "app-config"],

  function(Backbone, config) {

    var Materials = Backbone.Collection.extend({
      url: function(){
          if (this.caseStudyId != null)
            return config.api.keyflowsInCaseStudy.format(this.caseStudyId);
          else config.api.keyflows
      },
      
      initialize: function (options) {
        this.caseStudyId = options.caseStudyId;
      }
    });

    return Keyflows;
  }
);