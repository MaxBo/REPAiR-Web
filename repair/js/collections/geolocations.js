define(["backbone", "collections/gdsecollection", "models/geolocation"],

  function(Backbone, GDSECollection, Location) {
  

   /**
    *
    * @author Christoph Franke
    * @name module:collections/Locations
    * @augments Backbone.Collection
    */
    var Locations = GDSECollection.extend(
      /** @lends module:collections/Locations.prototype */
      {
      
      model: Location,
      
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
     * @returns {Array.<module:models/Location>} list of all locations belonging to the actor
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