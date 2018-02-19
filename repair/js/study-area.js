define([
  'd3',
  'visualizations/sankey-map',
  'views/study-area/base-maps',
  'app-config',
  'base'
], function(d3, MapView, BaseMapsView, appConfig) {

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
    var mapsView = new BaseMapsView({
      template: 'base-map-template',
      el: document.getElementById('base-map-setup'),
      casestudy: ''
    })
  }
  
  var session = appConfig.getSession(
    function(session){
      var mode = session['mode'];
      if (Number(mode) == 1) 
        renderSetup()
      else
        renderWorkshop()
  });
});