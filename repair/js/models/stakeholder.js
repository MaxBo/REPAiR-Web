define(["backbone", "app-config"],

  function(Backbone, config) {

    var Stakeholder = Backbone.Model.extend({

      urlRoot: config.api.stakeholders,
      idAttribute: "id",

      defaults: {
        id: '',
        name: ''
      },

    });
    return Stakeholder;
  }
);