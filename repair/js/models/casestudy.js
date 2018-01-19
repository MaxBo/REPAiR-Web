define(["backbone", "app-config"],

  function(Backbone, config) {

   /**
    *
    * model for fetching/putting a casestudy
    *
    * @param {Object} [attributes=null]  fields of the model and their values, will be set if passed
    *
    * @author Christoph Franke
    * @name module:models/CaseStudy
    * @augments Backbone.Model
    * @constructor
    * @see http://backbonejs.org/#Model
    */
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