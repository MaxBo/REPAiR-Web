define(["backbone", "app-config"],

  function(Backbone, config) {

    var Materials = Backbone.Collection.extend({
      url: config.api.materials
    });

    return Materials;
  }
);