define(["backbone", "app-config"],

  function(Backbone, config) {

   /**
    * @author Christoph Franke
    * @name module:collections/Areas
    * @augments Backbone.Collection
    */
    var Areas = Backbone.Collection.extend(
      /** @lends module:collections/Areas.prototype */
      {
      /**
       * generates an url to the api resource list based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      url: function(){
          if (this.caseStudyId != null)
            return config.api.areas.format(this.caseStudyId, this.levelId);
          else config.api.keyflows
      },
      
    /**
     * collection for fetching/putting areas
     *
     * @param {Array.<Object>} [attrs=null]   list objects representing the fields of each model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId    id of the casestudy the areas belong to
     * @param {string} options.levelId        id of the level the areas belong to
     *
     * @constructs
     * @see http://backbonejs.org/#Collection
     */
      initialize: function (attrs, options) {
        this.caseStudyId = options.caseStudyId;
        this.levelId = options.levelId;
      }
    });

    return Areas;
  }
);