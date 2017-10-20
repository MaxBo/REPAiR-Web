define(["backbone", "app-config"],

  function(Backbone, config) {

    var CaseStudy = Backbone.Model.extend({

      urlRoot: config.api.caseStudy,
      idAttribute: "id",

      defaults: {
        id: '',
        name: ''
      },

    });
    return CaseStudy;
  }
);