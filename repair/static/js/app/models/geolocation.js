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
          return url.format(this.caseStudyId, this.keyflowId);
      },

      initialize: function (attributes, options) {
        this.caseStudyId = options.caseStudyId;
        this.keyflowId = options.keyflowId;
        this.type = options.type;
        var geom = this.get("geometry");
        if (geom != null)
          this.setGeometry(geom.coordinates, geom.type);
          //this._previousAttributes = this.attributes;
          //geomObj._previousAttributes = geomObj.attributes;
        
      },
      
      defaults: {
        properties:  {}
      },
      
      setGeometry: function(coordinates, type){
        type = type || 'Point';
        var geomObj = new Geom({type: type, coordinates: coordinates});
        this.set("geometry", geomObj);
      }

    });
    return Location;
  }
);