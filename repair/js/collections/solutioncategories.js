define(["backbone", "models/solutioncategory", "app-config"],

  function(Backbone, SolutionCategory, config) {

   /**
    * @author Christoph Franke
    * @name module:collections/SolutionCategories
    * @augments Backbone.Collection
    */
    var SolutionCategories = Backbone.Collection.extend(
      /** @lends module:collections/SolutionCategories.prototype */
      {
      /**
       * generates an url to the api resource list based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      url: function(){
        return config.api.solutionCategories.format(this.caseStudyId);
      },
      
      model: SolutionCategory,
    
    /**
     * collection for fetching/putting categories of solutions
     *
     * @param {Array.<Object>} [attrs=null]   list objects representing the fields of each model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId  id of the casestudy the solutions belong to
     *
     * @constructs
     * @see http://backbonejs.org/#Collection
     */
      initialize: function (attrs, options) {
        this.caseStudyId = options.caseStudyId;
      }
    })
    return SolutionCategories;
  }
);