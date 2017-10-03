define([
  'd3',
  'map',
  'flowmap',
], function(d3, MapView, FlowMapView)
{

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

  var flowmap = new FlowMapView({
        divid: 'flowmap', 
        nodes: '/static/data/nodes.geojson', 
        links: '/static/data/links.csv'
    });
});