define(["backbone", "app-config"],

  function(Backbone, config) {

   /**
    * @author Christoph Franke
    * @name module:collections/AreaLevels
    * @augments Backbone.Collection
    */
    var AreaLevels = Backbone.Collection.extend(
      /** @lends module:collections/AreaLevels.prototype */
      {
      /**
       * generates an url to the api resource list based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      url: function(){
          return config.api.arealevels.format(this.caseStudyId);
      },
      
    /**
     * collection for fetching/putting levels of areas
     * sort() sorts by level 
     *
     * @param {Array.<Object>} [attrs=null]   list objects representing the fields of each model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId    id of the casestudy the levels belong to
     *
     * @constructs
     * @see http://backbonejs.org/#Collection
     */
      initialize: function (attrs, options) {
        this.caseStudyId = options.caseStudyId;
      },
      
      comparator: function(model) {
        return model.get('level');
      }
    });

    return AreaLevels;
  }
);