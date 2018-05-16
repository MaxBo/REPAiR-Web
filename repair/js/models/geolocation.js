define(["models/gdsemodel", "app-config"],

  function(GDSEModel, config) {
  
    var Geom = Backbone.Model.extend({
        defaults: {
            type: "Point",
            coordinates: [0, 0]
        }
    });
    
    var Location = GDSEModel.extend({
      /**
       * model for fetching/putting a location
       *
       * @param {Object} [attributes=null]      fields of the model and their values, will be set if passed
       * @param {Object} options
       * @param {string} options.baseurl        static url (overrides all of the follwing api arguments)
       * @param {string} options.apiTag         key of url as in config.api
       * @param {string} options.apiIds         ids to access api url (retrieved by apiTag), same order of appearance as in config.api[apiTag]
       *
       * @constructs
       * @see http://backbonejs.org/#Model
       */
        initialize: function (attributes, options) {
            // unfortunately super doesn't pass the arguments correctly
            //Location.__super__.initialize.apply(attributes, options);
            this.baseurl = options.url;
            this.apiTag = options.apiTag;
            this.apiIds = options.apiIds;
            
            var geom = this.get("geometry");
            if (geom != null)
              this.setGeometry(geom.coordinates, geom.type);
        },
        defaults: {
            properties:  {}
        },
        
      /**
       * set the geometry of the location
       *
       * @param {Array.<number>} coordinates  (x, y) coordinates
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
    return Location
  }
);