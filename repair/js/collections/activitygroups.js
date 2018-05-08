define(["backbone-pageable", "models/activitygroup", "app-config"],

  function(PageableCollection, ActivityGroup, config) {
  
   /**
    *
    * @author Christoph Franke
    * @name module:collections/ActivityGroups
    * @augments Backbone.PageableCollection
    *
    * @see https://github.com/backbone-paginator/backbone.paginator
    */
    var ActivityGroups = PageableCollection.extend(
      /** @lends module:collections/ActivityGroups.prototype */
      {
      /**
       * generates an url to the api resource list based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      url: function(){
        return config.api.activitygroups.format(this.caseStudyId, this.keyflowId);
      },
      
      state: {
          pageSize: 1000000,
          firstPage: 1,
          currentPage: 1
      }
      
      queryParams: {
        pageSize: "page_size"
      },
      
      parseRecords: function (response) {
        return response.results;
      },
      
    /**
     * collection of module:models/ActivityGroups
     *
     * @param {Array.<Object>} [attrs=null]   list objects representing the fields of each model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId  id of the casestudy the activitygroups belong to
     * @param {string} options.keyflowId    id of the keyflow the activitygroups belong to
     *
     * @constructs
     * @see http://backbonejs.org/#Collection
     */
      initialize: function (attrs, options) {
        this.caseStudyId = options.caseStudyId;
        this.keyflowId = options.keyflowId;
      },
      model: ActivityGroup
    });
    
    return ActivityGroups;
  }
);