define(["backbone", "app-config"],

  function(Backbone, config) {

    var Materials = Backbone.Collection.extend({
      url: function(){
          var url = (this.type == 'operational') ? config.api.opLocations: config.api.adminLocations
          return url.format(this.caseStudyId);
      },
      
      initialize: function (options) {
        this.caseStudyId = options.caseStudyId;
        this.type = options.type;
      }
    });

    return Materials;
  }
);