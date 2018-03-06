define(["backbone", "app-config"],

  function(Backbone, config) {

   /**
    *
    * @author Christoph Franke
    * @name module:models/Material
    * @augments Backbone.Model
    */
    var Material = Backbone.Model.extend(
      /** @lends module:models/Material.prototype */
      {
      idAttribute: "id",
      /**
       * generates an url to the api resource based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      urlRoot: function(){
        return config.api.materials.format(this.caseStudyId, this.keyflowId);
      },

    /**
     * model for fetching/putting an material
     *
     * @param {Object} [attributes=null]          fields of the model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId        id of the casestudy the material belongs to
     * @param {string} options.keyflowId          id of the keyflow the material belongs to
     *
     * @constructs
     * @see http://backbonejs.org/#Model
     */
      initialize: function (attributes, options) {
        this.caseStudyId = options.caseStudyId;
        this.keyflowId = options.keyflowId;
      },

    });
    return Material;
  }
);