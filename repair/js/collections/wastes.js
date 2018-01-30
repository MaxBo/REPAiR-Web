define(["backbone-pageable", "app-config"],

  function(PageableCollection, config) {

   /**
    * collection for fetching/putting waste products
    *
    * @param {Array.<Object>} [attrs=null]   list objects representing the fields of each model and their values, will be set if passed
    *
    * @author Christoph Franke
    * @name module:collections/Wastes
    * @augments Backbone.PageableCollection
    *
    * @constructor
    * @see https://github.com/backbone-paginator/backbone.paginator
    */
    var Wastes = PageableCollection.extend(
      /** @lends module:collections/Wastes.prototype */
      {
      /**
       * generates an url to the api resource list
       *
       * @returns {string} the url string
       */
      url: function(){
        return config.api.wastes;
      },
      
      queryParams: {
        pageSize: "page_size"
      },
      
      parseRecords: function (response) {
        return response.results;
      }
      
    });

    return Wastes;
  }
);