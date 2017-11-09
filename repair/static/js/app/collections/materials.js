define(["backbone", "app-config"],

  function(Backbone, Stakeholder, config) {

    var Materials = Backbone.Collection.extend({
      url: function(){
          return config.api.materials.format(this.caseStudyId);
      },
      
      initialize: function (options) {
        this.caseStudyId = options.caseStudyId;
      }
    });

    return Materials;
  }
);