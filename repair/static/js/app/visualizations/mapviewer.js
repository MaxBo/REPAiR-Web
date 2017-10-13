define([
  'leaflet',
  'esri-leaflet',
  'leaflet-fullscreen'
], function()
{
  var Map = function(options){
    var _this = this;

    var map = L.map(options.divid, {
        crs: L.CRS.EPSG4326,
        center: new L.LatLng(50,15),
        zoom: 4,
        fullscreenControl: true
    });
    
    $.each(options.baseLayers, function(name, layer) {
      layer.addTo(map);
    });
    //$.each(options.overlayLayers, function(name, layer) {
      //layer.addTo(map);
    //});
    
    L.control.layers(options.baseLayers, options.overlayLayers).addTo(map);
  };
  return Map
});