define(["backbone", "app/models/geolocation", "app-config"],

  function(Backbone, Geolocation, config) {

   /**
    *
    * @author Christoph Franke
    * @name module:collections/Locations
    * @augments Backbone.Collection
    */
    var Locations = Backbone.Collection.extend(
      /** @lends module:collections/Locations.prototype */
      {
      url: function(){
          var url = (this.loc_type == 'operational') ? config.api.opLocations: config.api.adminLocations
          return url.format(this.caseStudyId, this.keyflowId);
      },
      
    /**
     * collection of module:models/Location
     *
     * @param {Array.Object} [attrs=null]               list objects representing the fields of each model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId              id of the casestudy the location belongs to
     * @param {string} options.keyflowId                id of the keyflow the location belongs to
     * @param {string} [options.type='administrative']  type of location ('administrative' or 'operational')
     *
     * @constructs
     * @see http://backbonejs.org/#Collection
     */
      initialize: function (attrs, options) {
        this.caseStudyId = options.caseStudyId;
        this.loc_type = options.type;
        this.keyflowId = options.keyflowId;
      },
      model: Geolocation,
      
      //override
      parse: function(response) {
        // return the features as models of this collection, else you would only get one model regardless of feature-count
        return response.features;
      },
      
    /**
     * filter the collection to find models belonging to an actor with the given id
     *
     * @param {string} actorId id of the actor
     *
     * @returns {Array.module:models/Location} list of all locations belonging to the actor
     */
      filterActor: function (actorId) {
          var filtered = this.filter(function (loc) {
              return loc.get("properties").actor === actorId;
          });
          return filtered;
      }
    });

    return Locations;
  }
);