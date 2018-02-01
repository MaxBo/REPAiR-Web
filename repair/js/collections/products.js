define(["backbone-pageable", "app-config"],

  function(PageableCollection , config) {

   /**
    * collection for fetching/putting products
    *
    * @param {Array.<Object>} [attrs=null]   list objects representing the fields of each model and their values, will be set if passed
    * 
    * @author Christoph Franke
    * @name module:collections/Products
    * @augments Backbone.PageableCollection
    *
    * @constructor
    * @see https://github.com/backbone-paginator/backbone.paginator
    */
    var Products = PageableCollection.extend(
      /** @lends module:collections/Products.prototype */
      {
      /**
       * generates an url to the api resource
       *
       * @returns {string} the url string
       */
      url: function(){
        return config.api.products;
      },
      
      queryParams: {
        pageSize: "page_size"
      },
      
      parseRecords: function (response) {
        return response.results;
      }
    });

    return Products;
  }
);