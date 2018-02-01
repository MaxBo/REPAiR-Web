define(["backbone", "app-config"],

  function(Backbone, config) {

   /**
    *
    * @author Christoph Franke
    * @name module:models/Area
    * @augments Backbone.Model
    */
    var Area = Backbone.Model.extend(
      /** @lends module:models/Area.prototype */
      {
      idAttribute: "id",
      /**
       * generates an url to the api resource based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      urlRoot: function(){
        return config.api.areas.format(this.caseStudyId, this.levelId);
      },

    /**
     * model for fetching/putting an activitygroup
     *
     * @param {Object} [attributes=null]          fields of the model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId        id of the casestudy the area belongs to
     * @param {string} options.levelId            id of the level the area belongs to
     *
     * @constructs
     * @see http://backbonejs.org/#Model
     */
      initialize: function (attributes, options) {
        this.caseStudyId = options.caseStudyId;
        this.levelId = options.levelId;
      },

    });
    return Area;
  }
);