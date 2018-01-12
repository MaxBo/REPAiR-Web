define(["backbone", "app-config"],

  function(Backbone, config) {

   /**
    * @author Christoph Franke
    * @name module:collections/Products
    * @augments Backbone.Collection
    */
    var Products = Backbone.Collection.extend(
      /** @lends module:collections/Products.prototype */
      {
      /**
       * generates an url to the api resource list based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      url: function(){
        return config.api.products.format(this.caseStudyId, this.keyflowId);
      },
      
    /**
     * collection for fetching/putting products
     *
     * @param {Array.Object} [attrs=null]   list objects representing the fields of each model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId  id of the casestudy the products belong to
     * @param {string} options.keyflowId    id of the keyflow the products belong to
     *
     * @constructs
     * @see http://backbonejs.org/#Collection
     */
      initialize: function (attrs, options) {
        this.caseStudyId = options.caseStudyId;
        this.keyflowId = options.keyflowId;
      }
    });

    return Products;
  }
);