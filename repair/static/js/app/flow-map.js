define([
  'd3',
  'mapviewer',
], function(d3, MapViewer) {
  
  var bluemarble = L.tileLayer.wms('https://demo.boundlessgeo.com/geoserver/ows?', {
    layers: 'nasa:bluemarble'
  });
  
  var mapviewer = new MapViewer({
    divid: 'mapviewer',
    baseLayers: {"BlueMarble": bluemarble},
    overlayLayers: {}
  });
  
});