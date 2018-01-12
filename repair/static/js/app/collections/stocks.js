define(["backbone", "app-config"],

  function(Backbone, config) {
  
   /**
    * @author Christoph Franke
    * @name module:collections/Stocks
    * @augments Backbone.Collection
    */
    var Stocks = Backbone.Collection.extend(
      /** @lends module:collections/Stocks.prototype */
      {
      /**
       * generates an url to the api resource list based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      url: function(){
        var url = (this.type == 'activity') ? config.api.activityStock:
                  (this.type == 'actor') ? config.api.actorStock:
                  config.api.groupStock;
        return url.format(this.caseStudyId, this.keyflowId);
      },
      
    /**
     * collection for fetching/putting stocks
     *
     * @param {Array.Object} [attrs=null]     list objects representing the fields of each model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId    id of the casestudy the stocks belong to
     * @param {string} options.keyflowId      id of the keyflow the stocks belong to
     * @param {string} [options.type='group'] type of nodes connected to the stocks ('activity', 'actor' or 'group')
     *
     * @constructs
     * @see http://backbonejs.org/#Collection
     */
      initialize: function (attrs, options) {
        this.caseStudyId = options.caseStudyId;
        this.keyflowId = options.keyflowId;
        this.type = options.type;
      },
    });
    
    return Stocks;
  }
);