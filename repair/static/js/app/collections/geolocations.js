define(["backbone", "app/models/geolocation", "app-config"],

  function(Backbone, Geolocation, config) {

    var Locations = Backbone.Collection.extend({
      url: function(){
          var url = (this.loc_type == 'operational') ? config.api.opLocations: config.api.adminLocations
          return url.format(this.caseStudyId, this.keyflowId);
      },
      
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