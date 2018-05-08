define(["backbone-pageable", "models/activity", "app-config"],

  function(PageableCollection, Activity, config) {
  
   /**
    *
    * @author Christoph Franke
    * @name module:collections/Activities
    * @augments Backbone.PageableCollection
    *
    * @see https://github.com/backbone-paginator/backbone.paginator
    */
    var Activities = PageableCollection.extend(
      /** @lends module:collections/Activities.prototype */
      {
      /**
       * generates an url to the api resource list based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      url: function(){
          return config.api.activities.format(this.caseStudyId, this.keyflowId);
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
     * collection of module:models/Activity
     *
     * @param {Array.<Object>} [attrs=null]         list objects representing the fields of each model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId        id of the casestudy the activities belong to
     * @param {string} options.activityGroupCode  id of the activitygroup the activities belong to
     * @param {string} options.keyflowId          id of the keyflow the activities belong to
     *
     * @constructs
     * @see http://backbonejs.org/#Collection
     */
      initialize: function (attrs, options) {
        this.caseStudyId = options.caseStudyId;
        this.keyflowId = options.keyflowId;
      },
      
      /**
       * filter the collection to find models belonging to an activitygroup with the given id
       *
       * @param {string} groupId id of the group
       *
       * @returns {Array.<module:models/Activity>} list of all activities belonging to the group
       */
      filterGroup: function (groupId) {
          var filtered = this.filter(function (activity) {
              return activity.get("activitygroup") == groupId;
          });
          return filtered;
      },
      
      model: Activity
    });
    
    return Activities;
  }
);