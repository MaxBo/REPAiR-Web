define(["backbone", "models/chart", "app-config"],

  function(Backbone, Chart, config) {

   /**
    * @author Christoph Franke
    * @name module:collections/Charts
    * @augments Backbone.Collection
    */
    var Charts = Backbone.Collection.extend(
      /** @lends module:collections/Charts.prototype */
      {
      /**
       * generates an url to the api resource list based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      url: function(){
        return config.api.charts.format(this.caseStudyId, this.chartCategoryId);
      },
      
      model: Chart,
    
    /**
     * collection for fetching/putting charts
     *
     * @param {Array.<Object>} [attrs=null]    list objects representing the fields of each model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId     id of the casestudy the chart belongs to
     * @param {string} options.chartCategoryId id of the category the chart belongs to
     *
     * @constructs
     * @see http://backbonejs.org/#Collection
     */
      initialize: function (attrs, options) {
        this.caseStudyId = options.caseStudyId;
        this.chartCategoryId = options.chartCategoryId;
      }
    })
    return Charts;
  }
);