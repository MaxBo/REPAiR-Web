define(["backbone", "app-config"],

  function(Backbone, config) {

   /**
    *
    * @author Christoph Franke
    * @name module:models/Solution
    * @augments Backbone.Model
    */
    var Solution = Backbone.Model.extend(
      /** @lends module:models/Solution.prototype */
      {
      idAttribute: "id",
      
      defaults: {
        name: '-----',
        description: '',
        one_unit_equals: '',
        service_layers: '',
        activities: [],
        activities_image: null,
        currentstate_image: null,
        effect_image: null
      },
      
      /**
       * generates an url to the api resource based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      urlRoot: function(){
        return config.api.solutions.format(this.caseStudyId, this.solutionCategoryId);
      },

    /**
     * model for fetching/putting defintions of a solution
     *
     * @param {Object} [attributes=null]          fields of the model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId        id of the casestudy the solution belong to
     * @param {string} options.solutionCategoryId id of the category the solution belong to
     *
     * @constructs
     * @see http://backbonejs.org/#Model
     */
      initialize: function (attributes, options) {
        this.caseStudyId = options.caseStudyId;
        this.solutionCategoryId = options.solutionCategoryId;
      },

    });
    return Solution;
  }
);