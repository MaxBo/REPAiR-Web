define(["backbone", "models/chartcategory", "app-config"],

  function(Backbone, ChartCategory, config) {

   /**
    * @author Christoph Franke
    * @name module:collections/ChartCategories
    * @augments Backbone.Collection
    */
    var ChartCategories = Backbone.Collection.extend(
      /** @lends module:collections/ChartCategories.prototype */
      {
      /**
       * generates an url to the api resource list based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      url: function(){
        return config.api.chartCategories.format(this.caseStudyId);
      },
      
      model: ChartCategory,
    
    /**
     * collection for fetching/putting categories of charts
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
    return ChartCategories;
  }
);