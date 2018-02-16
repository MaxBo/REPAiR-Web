define(["backbone"],
function (Backbone) {

  var GEOSERVER_URL = 'https://geoserver.h2020repair.bk.tudelft.nl/geoserver';
  
  var Layer = Backbone.Model.extend({
    url: '',
    //override
    parse: function(response) {
      return response.featureType;
    },
    wmsRequestUrl: function(options){
      var options = options || {};
      var epsg = options.epsg || 'EPSG:3857';
      var identifier = this.get('name') + ':' + this.get('namespace').name;
      return 'wms?service=WMS&version=1.1.0&request=GetMap&layers=' + identifier +'&styles=&srs=' + epsg + '&format=application/openlayers';
    }
  });

  class Geoserver {
  
    constructor(options){
      var options = options || {};
      
      var _this = this;
      this.url = GEOSERVER_URL;
      
      this.restApi =  {
        base: '/rest',
        workspaces: '/rest/workspaces',
        layers: '/rest/layers'
      };
      
      this.credentials = {
        user: options.user,
        pass: options.pass,
        auth: { "Authorization": "Basic " + btoa(options.user + ":" + options.pass) }
      };
      
      var Layers = Backbone.Collection.extend({
        url: _this.url  + _this.restApi.layers,
        
        //override
        parse: function(response) {
          // geoserver api makes a nesting at list view 
          return response.layers.layer;
        },
      });
      this.layers = new Layers();
    }
        
    login(user, pass){
      this.credentials.user = user;
      this.credentials.pass = pass;
      this.credentials.auth = { "Authorization": "Basic " + btoa(user + ":" + pass) };
      var request = new XMLHttpRequest();
      var url = this.url + this.api.base + '/workspaces';
      //var url = this.url + '/wfs?Request=GetCapabilities';
      request.open('GET', url, true);
      request.setRequestHeader("Authorization", "Basic " + btoa(user + ":" + pass));
      request.send();
      function processRequest(e) {
        console.log(e)
      }
      request.onreadystatechange = processRequest;
    }
    
    getLayers(options){
      var options = options || {};
      this.layers.fetch({ 
        headers: this.credentials.auth, 
        success: options.success || function(){}, 
        error: options.error || function(){}
      });
    }
    
    getLayer(url, options){
      var options = options || {};
      var _this = this;
      // urls provided by geoserver start with http:
      url = url.replace('http:', 'https:');
  
      // geoserver references to an url that references to the actual resource (strange nesting again)
      var LayerInfo = Backbone.Model.extend({ url: url });
      var layerInfo = new LayerInfo();
      layerInfo.noTrail = true;
      layerInfo.fetch({ 
        headers: this.credentials.auth, 
        success: function(model, response){
          console.log(model)
          var redUrl = model.get('layer').resource.href;
          redUrl = redUrl.replace('http:', 'https:');
          var layer = new Layer();
          layer.url = redUrl;
          layer.noTrail = true;
          layer.fetch({
            headers: _this.credentials.auth, 
            success: options.success || function(){},
            error: options.error || function(){}
          })
        }, 
        error: options.error || function(){}
      });
    }
  }
  return Geoserver;
});