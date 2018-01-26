define(["backbone", "app-config"],

  function(Backbone, config) {

   /**
    * @author Christoph Franke
    * @name module:collections/Publications
    * @augments Backbone.Collection
    */
    var Publications = Backbone.Collection.extend(
      /** @lends module:collections/Actors.prototype */
      {
      /**
       * generates an url to the api resource list based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      url: function(){
        // if an caseStudyId is given, take the route that retrieves publications in that casestudy
        if (this.caseStudyId != null)
          return config.api.publicationsInCasestudy.format(this.caseStudyId);
        // if no caseStudyId is given, get all publications
        else
          return config.api.publications;
      },
      
      
    /**
     * collection for fetching/putting publications
     *
     * @param {Array.<Object>} [attrs=null]   list objects representing the fields of each model and their values, will be set if passed
     * @param {Object} options
     * @param {string=} options.caseStudyId   id of the casestudy the publications belong to (if not given all casestudies)
     *
     * @constructs
     * @see http://backbonejs.org/#Collection
     */
      initialize: function (attrs, options) {
        this.caseStudyId = options.caseStudyId;
      },
    });

    return Publications;
  }
);