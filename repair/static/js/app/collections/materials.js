define(["backbone", "app-config"],

  function(Backbone, config) {

    var Materials = Backbone.Collection.extend({
      url: function(){
          if (this.caseStudyId != null)
            return config.api.materialsInCaseStudy.format(this.caseStudyId);
          else config.api.materials
      },
      
      initialize: function (options) {
        this.caseStudyId = options.caseStudyId;
      }
    });

    return Materials;
  }
);