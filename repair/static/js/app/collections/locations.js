define(["backbone", "app-config"],

  function(Backbone, config) {

    var Locations = Backbone.Collection.extend({
      url: function(){
          var url = (this.type == 'operational') ? config.api.opLocations: config.api.adminLocations
          return url.format(this.caseStudyId);
      },
      
      initialize: function (options) {
        this.caseStudyId = options.caseStudyId;
        this.type = options.type;
      },
      //override
      parse: function(response) {
        // return the features as models of this collection, else you would only get one model regardless of feature-count
        return response.features;
      },
      
      filterActor: function (actorId) {
          var filtered = this.filter(function (loc) {
              return loc.get("properties").actor === actorId;
          });
          //return new Locations(filtered);
          return filtered
      }
    });

    return Locations;
  }
);