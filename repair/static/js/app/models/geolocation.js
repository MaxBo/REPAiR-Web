define(["backbone", "app-config"],

  function(Backbone, config) {
  
    var Geom = Backbone.Model.extend({
        defaults: {
            type: "Point",
            coordinates: [0, 0]
        }
    });

    var Location = Backbone.Model.extend({
      idAttribute: "id",
      tag: "activity",
      urlRoot: function(){
          var url = (this.type == 'operational') ? config.api.opLocations: config.api.adminLocations
          return url.format(this.caseStudyId);
      },

      initialize: function (options) {
        this.caseStudyId = options.caseStudyId;
        this.type = options.type;
        var geom = this.get("geometry");
        if (geom != null){
          var geomObj = new Geom({type: geom.type, coordinates: geom.coordinates});
          this.set("geometry", geomObj);
          //this._previousAttributes = this.attributes;
          //geomObj._previousAttributes = geomObj.attributes;
        }
      },

    });
    return Location;
  }
);