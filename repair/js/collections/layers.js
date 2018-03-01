define(["backbone", "models/layer", "app-config"],

  function(Backbone, Layer, config) {

   /**
    * @author Christoph Franke
    * @name module:collections/Layers
    * @augments Backbone.Collection
    */
    var Layers = Backbone.Collection.extend(
      /** @lends module:collections/Layers.prototype */
      {
      /**
       * generates an url to the api resource list based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      url: function(){
        return config.api.layers.format(this.caseStudyId, this.layerCategoryId);
      },
      
      model: Layer,
    
    /**
     * collection for fetching/putting definitions of service layers
     *
     * @param {Array.<Object>} [attrs=null]    list objects representing the fields of each model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId     id of the casestudy the service layer definitions belong to
     * @param {string} options.layerCategoryId id of the category the layer defintions belong to
     *
     * @constructs
     * @see http://backbonejs.org/#Collection
     */
      initialize: function (attrs, options) {
        this.caseStudyId = options.caseStudyId;
        this.layerCategoryId = options.layerCategoryId;
      }
    })
    return Layers;
  }
);