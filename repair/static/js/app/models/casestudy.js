define(["backbone", "app-config"],

  function(Backbone, config) {

    var CaseStudy = Backbone.Model.extend({

      urlRoot: config.api.casestudies,
      idAttribute: "id",

      defaults: {
        id: '',
        name: ''
      },

    });
    return CaseStudy;
  }
);