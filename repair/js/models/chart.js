define(["backbone", "app-config"],

  function(Backbone, config) {

   /**
    *
    * @author Christoph Franke
    * @name module:models/Chart
    * @augments Backbone.Model
    */
    var Chart = Backbone.Model.extend(
      /** @lends module:models/Chart.prototype */
      {
      idAttribute: "id",
      
      defaults: {
        name: '-----',
        image: null
      },
      
      /**
       * generates an url to the api resource based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      urlRoot: function(){
        return config.api.charts.format(this.caseStudyId, this.chartCategoryId);
      },

    /**
     * model for fetching/putting a chart
     *
     * @param {Object} [attributes=null]       fields of the model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId     id of the casestudy the chart belongs to
     * @param {string} options.chartCategoryId id of the category the chart belongs to
     *
     * @constructs
     * @see http://backbonejs.org/#Model
     */
      initialize: function (attributes, options) {
        this.caseStudyId = options.caseStudyId;
        this.chartCategoryId = options.chartCategoryId;
      },

    });
    return Chart;
  }
);