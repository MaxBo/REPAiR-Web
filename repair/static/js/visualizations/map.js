define([
  'd3',
  'spatialsankey',
  'leaflet'
], function(d3, spatialsankey)
{
  var Map = function(options){
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
     
    // Initialize the SVG layer
    map._initPathRoot()
    
    // Setup svg element to work with
    var svg = d3.select('#' + options.divid).select("svg"),
        linklayer = svg.append("g"),
        nodelayer = svg.append("g");
    
    var n = options.nodes;
    var l = options.links;
    
    // Load data asynchronosuly
    d3.json(n, function(nodes) {
      d3.csv(l, function(links) {
      
        // Setup spatialsankey object
        var sankey = d3.spatialsankey()
                              .lmap(map)
                              .nodes(nodes.features)
                              .links(links);
        var mouseover = function(d){
          // Get link data for this node
          var nodelinks = sankey.links().filter(function(link){
            return link.source == d.id;
          });
    
          // Add data to link layer
          var beziers = linklayer.selectAll("path").data(nodelinks);
          link = sankey.link(options);
    
          // Draw new links
          beziers.enter()
            .append("path")
            .attr("d", link)
            .attr('id', function(d){return d.id})
            .style("stroke-width", sankey.link().width());
          
          // Remove old links
          beziers.exit().remove();
    
          // Hide inactive nodes
          var circleUnderMouse = this;
          circs.transition().style('opacity',function () {
              return (this === circleUnderMouse) ? 0.7 : 0;
          });
        };
    
        var mouseout = function(d) {
          // Remove links
          linklayer.selectAll("path").remove();
          // Show all nodes
          circs.transition().style('opacity', 0.7);
        };
    
        // Draw nodes
        var node = sankey.node()
        var circs = nodelayer.selectAll("circle")
          .data(sankey.nodes())
          .enter()
          .append("circle")
          .attr("cx", node.cx)
          .attr("cy", node.cy)
          .attr("r", node.r)
          .style("fill", node.fill)
          .attr("opacity", 0.7)
          .on('mouseover', mouseover)
          .on('mouseout', mouseout);
        
        // Adopt size of drawn objects after leaflet zoom reset
        var zoomend = function(){
            linklayer.selectAll("path").attr("d", sankey.link());
    
            circs.attr("cx", node.cx)
                 .attr("cy", node.cy);
        };
     
        map.on("zoomend", zoomend);
      });
    });
    var options = {'use_arcs': false, 'flip': false};
    d3.selectAll("input").forEach(function(x){
      options[x.name] = parseFloat(x.value);
    })
    
    d3.selectAll("input").on("click", function(){
      options[this.name] = parseFloat(this.value);
    });
  };
  return Map
});