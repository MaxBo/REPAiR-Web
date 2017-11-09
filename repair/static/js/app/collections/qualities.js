define(["backbone","app/models/stakeholder", "app-config"],

  function(Backbone, Stakeholder, config) {

    var Qualities = Backbone.Collection.extend({
      url: config.api.qualities
    });

    return Qualities;
  }
);