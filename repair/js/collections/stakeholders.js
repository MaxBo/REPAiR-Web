define(["backbone","models/stakeholder", "app-config"],

  function(Backbone, Stakeholder, config) {

   /**
    * collection for fetching/putting stakeholders
    *
    * @param {Object} [attributes=null]  fields of the model and their values, will be set if passed
    *
    * @author Christoph Franke
    * @name module:collections/Stakeholders
    * @augments Backbone.Collection
    * @constructor
    * @see http://backbonejs.org/#Collection
    */
    var Stakeholders = Backbone.Collection.extend({
      url: config.api.stakeholders,
      model: Stakeholder
    });

    return Stakeholders;
  }
);