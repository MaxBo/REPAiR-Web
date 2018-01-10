define(["backbone", "models/casestudy", "app-config"],

  function(Backbone, CaseStudy, config) {

    var CaseStudies = Backbone.Collection.extend({
      url: config.api.casestudies
    });

    return CaseStudies;
  }
);