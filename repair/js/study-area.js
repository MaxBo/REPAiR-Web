define([
  'd3',
  'visualizations/sankey-map',
  'visualizations/map',
  'app-config', 'geoserver',
  'base'
], function(d3, MapView, Map, appConfig, Geoserver) {

  function renderWorkshop(){
    NodeHandler = function(){
      this.id = 0;
      var callbacks = [];
      
      this.add = function(callback){
        callbacks.push(callback);
      }
      
      this.changeActive = function(id){
        this.id = id;
        callbacks.forEach(function(callback){
          callback(id);
        });
      }
    }
  
    var handler = new NodeHandler();
    
    var callbackTest = function(id){
      document.getElementById('nodeinfo').innerHTML = "Node ID: " + id;
    }
    
    handler.add(callbackTest);
    
    var map = new MapView({
      divid: 'map', 
      nodes: '/static/data/nodes.geojson', 
      links: '/static/data/links.csv',
      nodeHandler: handler
    });
  }
  
  function renderSetup(){
    //var map = new Map({
        //divid: 'edit-location-map', 
      //});
    var geoserver = new Geoserver({ user: '', pass: '' });
    geoserver.getLayers({ success: function(layers){
      console.log(layers);
      geoserver.getLayer(layers.first().get('href'), { success: function(layer) { console.log(layer)}})
    }});
  }
  
  var session = appConfig.getSession(
    function(session){
      var mode = session['mode'];
      console.log(mode)
      if (Number(mode) == 1) 
        renderSetup()
      else
        renderWorkshop()
  });
});