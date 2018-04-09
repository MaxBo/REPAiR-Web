define(["backbone-pageable", "app-config"],

  function(PageableCollection, config) {

   /**
    * collection for fetching/putting products
    *
    * @param {Array.<Object>} [attrs=null]   list objects representing the fields of each model and their values, will be set if passed
    *
    * @author Balázs Dukai
    * @name module:collections/TargetValues
    * @augments Backbone.PageableCollection
    *
    * @constructor
    * @see https://github.com/backbone-paginator/backbone.paginator
    */
    var TargetValues = PageableCollection.extend(
      /** @lends module:collections/TargetValues.prototype */
      {
      /**
       * generates an url to the api resource
       *
       * @returns {string} the url string
       */
      url: function(){
        return config.api.targetvalues;
      },

      queryParams: {
        pageSize: "page_size"
      },

      parseRecords: function (response) {
        return response.results;
      }
    });

    return TargetValues;
  }
);
