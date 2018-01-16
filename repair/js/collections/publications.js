define(["backbone", "app-config"],

  function(Backbone, config) {

   /**
    * collection for fetching/putting publications
    *
    * @param {Object} [attributes=null]  fields of the model and their values, will be set if passed
    *
    * @author Christoph Franke
    * @name module:collections/Publications
    * @augments Backbone.Model
    * @constructor
    * @see http://backbonejs.org/#Collection
    */
    var Publications = Backbone.Collection.extend({
      url: config.api.publications
    });

    return Publications;
  }
);