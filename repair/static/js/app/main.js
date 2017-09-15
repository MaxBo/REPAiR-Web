define([
  'd3',
  'map'
], function(d3, MapView)
{
  var map = new MapView({
        divid: 'map', 
        nodes: '/static/data/nodes.geojson', 
        links: '/static/data/links.csv'
    });
});