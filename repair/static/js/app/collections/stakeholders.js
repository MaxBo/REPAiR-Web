define(["backbone","app/models/stakeholder", "app-config"],

  function(Backbone, Stakeholder, config) {

    var Stakeholders = Backbone.Collection.extend({
      url: config.api.stakeholders,
      model: Stakeholder
    });

    return Stakeholders;
  }
);