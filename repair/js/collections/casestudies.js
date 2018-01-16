define(["backbone", "models/casestudy", "app-config"],

  function(Backbone, CaseStudy, config) {

   /**
    * collection for fetching/putting casestudies
    *
    * @param {Object} [attributes=null]  fields of the model and their values, will be set if passed
    *
    * @author Christoph Franke
    * @name module:collections/CaseStudies
    * @augments Backbone.Model
    * @constructor
    * @see http://backbonejs.org/#Collection
    */
    var CaseStudies = Backbone.Collection.extend({
      url: config.api.casestudies
    });

    return CaseStudies;
  }
);