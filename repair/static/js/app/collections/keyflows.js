define(["backbone", "app-config"],

  function(Backbone, config) {

   /**
    * @author Christoph Franke
    * @name module:collections/Keyflows
    * @augments Backbone.Collection
    */
    var Keyflows = Backbone.Collection.extend(
      /** @lends module:collections/Keyflows.prototype */
      {
      /**
       * generates an url to the api resource list based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      url: function(){
          if (this.caseStudyId != null)
            return config.api.keyflowsInCaseStudy.format(this.caseStudyId);
          else config.api.keyflows
      },
      
    /**
     * collection for fetching/putting keyflows
     *
     * @param {Array.Object} [attrs=null]   list objects representing the fields of each model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId  id of the casestudy the keyflows belong to
     *
     * @constructs
     * @see http://backbonejs.org/#Collection
     */
      initialize: function (attrs, options) {
        this.caseStudyId = options.caseStudyId;
      }
    });

    return Keyflows;
  }
);