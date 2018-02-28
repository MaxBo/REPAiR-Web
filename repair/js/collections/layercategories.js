define(["backbone", "app-config"],

  function(Backbone, config) {

   /**
    * @author Christoph Franke
    * @name module:collections/LayerCategories
    * @augments Backbone.Collection
    */
    var LayerCategories = Backbone.Collection.extend(
      /** @lends module:collections/LayerCategories.prototype */
      {
      /**
       * generates an url to the api resource list based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      url: function(){
        return config.api.layerCategories.format(this.caseStudyId);
      },
    
    /**
     * collection for fetching/putting categories of service layer definitions
     *
     * @param {Array.<Object>} [attrs=null]   list objects representing the fields of each model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId  id of the casestudy the categories belong to
     *
     * @constructs
     * @see http://backbonejs.org/#Collection
     */
      initialize: function (attrs, options) {
        this.caseStudyId = options.caseStudyId;
      }
    })
    return LayerCategories;
  }
);