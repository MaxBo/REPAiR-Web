define(["backbone", "app-config"],

  function(Backbone, config) {

   /**
    * collection for fetching/putting materials
    *
    * @param {Object} [attributes=null]  fields of the model and their values, will be set if passed
    *
    * @author Christoph Franke
    * @name module:collections/Materials
    * @augments Backbone.Collection
    * @constructor
    * @see http://backbonejs.org/#Collection
    */
    var Materials = Backbone.Collection.extend({
      url: config.api.materials
    });

    return Materials;
  }
);