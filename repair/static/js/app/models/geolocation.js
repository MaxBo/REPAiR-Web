define(["backbone", "app-config"],

  function(Backbone, config) {
  
    var Geom = Backbone.Model.extend({
        defaults: {
            type: "Point",
            coordinates: [0, 0]
        }
    });

   /**
    *
    * @author Christoph Franke
    * @name module:models/Location
    * @augments Backbone.Model
    */
    var Location = Backbone.Model.extend(
      /** @lends module:models/Location.prototype */
      {
      idAttribute: "id",
      tag: "activity",
      /**
       * generates an url to the api resource based on the ids and type given in constructor
       *
       * @returns {string} the url string
       */
      urlRoot: function(){
          var loc_type = (this.collection != null) ? this.collection.loc_type: this.loc_type;
          var url = (loc_type == 'operational') ? config.api.opLocations: config.api.adminLocations
          return url.format(this.caseStudyId, this.keyflowId);
      },

    /**
     * model for fetching/putting a location
     *
     * @param {Object} [attributes=null]                  fields of the model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId                id of the casestudy the location belongs to
     * @param {string} options.keyflowId                  id of the keyflow the location belongs to
     * @param {string} [options.type='administrative']    type of location ('administrative' or 'operational')
     *
     * @constructs
     * @see http://backbonejs.org/#Model
     */
      initialize: function (attributes, options) {
        this.caseStudyId = options.caseStudyId;
        this.keyflowId = options.keyflowId;
        this.loc_type = options.type;
        var geom = this.get("geometry");
        if (geom != null)
          this.setGeometry(geom.coordinates, geom.type);
          //this._previousAttributes = this.attributes;
          //geomObj._previousAttributes = geomObj.attributes;
        
      },
  
      defaults: {
        properties:  {}
      },
      
    /**
     * set the geometry of the location
     *
     * @param {Array.number} coordinates  (x, y) coordinates
     * @param {string} [type='Point']     type of geometry
     *
     * @see http://backbonejs.org/#Model
     */
      setGeometry: function(coordinates, type){
        type = type || 'Point';
        var geomObj = new Geom({type: type, coordinates: coordinates});
        this.set("geometry", geomObj);
      }

    });
    return Location;
  }
);