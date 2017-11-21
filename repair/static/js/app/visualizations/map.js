define([
  'leaflet',
  'esri-leaflet',
  'leaflet-fullscreen'
], function()
{
  var Map = function(options){
    
    var map = L.map(options.divid, {
        crs: L.CRS.EPSG4326,
        center: new L.LatLng(50,15),
        zoom: 4,
        fullscreenControl: true
    });

    var marker = L.marker(new L.LatLng(50,15), {draggable: 'true'}).addTo(map);
    marker.bindPopup(marker.getLatLng().lat + ', ' + marker.getLatLng().lng);
    
    marker.on('dragend', function(event){
      var marker = event.target;
      var position = marker.getLatLng();
      marker.setLatLng(new L.LatLng(position.lat, position.lng),{draggable:'true'});
      map.panTo(new L.LatLng(position.lat, position.lng));
      marker.bindPopup(marker.getLatLng().lat + ', ' + marker.getLatLng().lng);
    });
    
    $.each(options.baseLayers, function(name, layer) {
      layer.addTo(map);
    });
    
    L.control.layers(options.baseLayers, options.overlayLayers).addTo(map);
    
    function onMapClick(e) {
        marker.setLatLng(e.latlng);
        marker.bindPopup(marker.getLatLng().lat + ', ' + marker.getLatLng().lng);
    }
    map.doubleClickZoom.disable(); 
    map.on('dblclick', onMapClick);
  };
  
  
  return Map
});