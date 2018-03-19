define(["backbone", "app-config"],

  function(Backbone, config) {

   /**
    *
    * @author Christoph Franke
    * @name module:models/Layer
    * @augments Backbone.Model
    */
    var Layer = Backbone.Model.extend(
      /** @lends module:models/Layer.prototype */
      {
      idAttribute: "id",
      
      defaults: {
        name: '-----',
        description: '',
        credentials_needed: false,
        service_version: '',
        service_layers: '',
        url: '',
        is_repair_layer: false
      },
      
      /**
       * generates an url to the api resource based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      urlRoot: function(){
        return config.api.layers.format(this.caseStudyId, this.layerCategoryId);
      },

    /**
     * model for fetching/putting defintions of a service layer
     *
     * @param {Object} [attributes=null]       fields of the model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId     id of the casestudy the layer defintion belongs to
     * @param {string} options.layerCategoryId id of the category the layer defintion belongs to
     *
     * @constructs
     * @see http://backbonejs.org/#Model
     */
      initialize: function (attributes, options) {
        this.caseStudyId = options.caseStudyId;
        this.layerCategoryId = options.layerCategoryId;
      },

    });
    return Layer;
  }
);