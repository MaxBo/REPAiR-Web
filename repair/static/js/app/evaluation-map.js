define([
  'd3',
  'mapviewer',
], function(d3, MapViewer) {

  var evaluationmap = new MapViewer({
    divid: 'evaluationmap', 
    baseLayers: {"Stamen map tiles": new L.tileLayer('http://{s}tile.stamen.com/toner-lite/{z}/{x}/{y}.png', {
          subdomains: ['','a.','b.','c.','d.'],
          attribution: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC BY SA</a>'
        })},
    overlayLayers: {}
  });
  
});