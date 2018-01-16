define([
  'd3',
  'visualizations/sankey-map',
], function(d3, MapView) {
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
});