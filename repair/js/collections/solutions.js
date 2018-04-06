define(["backbone", "models/solution", "app-config"],

  function(Backbone, Solution, config) {

   /**
    * @author Christoph Franke
    * @name module:collections/Solutions
    * @augments Backbone.Collection
    */
    var Solutions = Backbone.Collection.extend(
      /** @lends module:collections/Solutions.prototype */
      {
      /**
       * generates an url to the api resource list based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      url: function(){
        return config.api.solutions.format(this.caseStudyId, this.solutionCategoryId);
      },
      
      model: Solution,
    
    /**
     * collection for fetching/putting solutions
     *
     * @param {Array.<Object>} [attrs=null]      list objects representing the fields of each model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId        id of the casestudy the solutions belong to
     * @param {string} options.solutionCategoryId id of the category the solutions belong to
     *
     * @constructs
     * @see http://backbonejs.org/#Collection
     */
      initialize: function (attrs, options) {
        this.caseStudyId = options.caseStudyId;
        this.solutionCategoryId = options.solutionCategoryId;
      }
    })
    return Solutions;
  }
);