define(["backbone", "app/models/casestudy", "app-config"],

  function(Backbone, CaseStudy, config) {

    var CaseStudies = Backbone.Collection.extend({
      url: config.api.casestudies,
      model: CaseStudy
    });

    return CaseStudies;
  }
);