define([
  'd3',
  'spatialsankey',
  'leaflet'
], function(d3, spatialsankey)
{
  var Map = function(options){
    
    this.nodes = options.nodes;
    this.links = options.links;
    this.handler = options.nodeHandler;
    var _this = this;
    
    // Set leaflet map
    var map = new L.map(options.divid, {
      center: new L.LatLng(50,15),
      zoom: 4,
      layers: [
        new L.tileLayer('http://{s}tile.stamen.com/toner-lite/{z}/{x}/{y}.png', {
          subdomains: ['','a.','b.','c.','d.'],
          attribution: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC BY SA</a>'
        })
      ]
    });
  };
  return Map
});