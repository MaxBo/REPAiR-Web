define(["backbone", "app/models/activitygroup", "app-config"],

  function(Backbone, ActivityGroup, config) {
  
   /**
    *
    * @author Christoph Franke
    * @name module:collections/ActivityGroups
    * @augments Backbone.Collection
    */
    var ActivityGroups = Backbone.Collection.extend(
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
      
    /**
     * collection of module:models/ActivityGroups
     *
     * @param {Array.Object} [attrs=null]   list objects representing the fields of each model and their values, will be set if passed
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