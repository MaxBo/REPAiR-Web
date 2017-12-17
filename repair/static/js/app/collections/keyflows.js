define(["backbone", "app-config"],

  function(Backbone, config) {

    var Keyflows = Backbone.Collection.extend({
      url: function(){
          if (this.caseStudyId != null)
            return config.api.keyflowsInCaseStudy.format(this.caseStudyId);
          else config.api.keyflows
      },
      
      initialize: function (attrs, options) {
        this.caseStudyId = options.caseStudyId;
      }
    });

    return Keyflows;
  }
);