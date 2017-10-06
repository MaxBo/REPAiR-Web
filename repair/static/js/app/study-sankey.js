define([
  'd3',
  'map',
  'flowmap',
  'mapviewer',
], function(d3, MapView, FlowMapView, MapViewer)
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
  
  var evaluationmap = new MapViewer({
    divid: 'evaluationmap', 
    baseLayers: {"Stamen map tiles": new L.tileLayer('http://{s}tile.stamen.com/toner-lite/{z}/{x}/{y}.png', {
          subdomains: ['','a.','b.','c.','d.'],
          attribution: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC BY SA</a>'
        })},
    overlayLayers: {}
  });
  
  var bluemarble = L.tileLayer.wms('https://demo.boundlessgeo.com/geoserver/ows?', {
    layers: 'nasa:bluemarble'
  });
  
  var mapviewer = new MapViewer({
    divid: 'mapviewer',
    baseLayers: {"BlueMarble": bluemarble},
    overlayLayers: {}
  });
});