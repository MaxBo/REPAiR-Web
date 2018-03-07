define(["backbone", "models/material", "app-config"],

  function(Backbone, Material, config) {

   /**
    * @author Christoph Franke
    * @name module:collections/Materials
    * @augments Backbone.Collection
    */
    var Materials = Backbone.Collection.extend(
      /** @lends module:collections/Materials.prototype */
      {
      /**
       * generates an url to the api resource list based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      url: function(){
        return config.api.materials.format(this.caseStudyId, this.keyflowId);
      },
      
      model: Material,
    
    /**
     * collection for fetching/putting materials
     *
     * @param {Array.<Object>} [attrs=null]   list objects representing the fields of each model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId  id of the casestudy the materials belong to
     * @param {string} options.keyflowId    id of the keyflow the materials belong to
     *
     * @constructs
     * @see http://backbonejs.org/#Collection
     */
      initialize: function (attrs, options) {
        this.caseStudyId = options.caseStudyId;
        this.keyflowId = options.keyflowId;
      }
    })
    return Materials;
  }
);