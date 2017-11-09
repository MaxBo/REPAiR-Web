define([
  'd3',
  'cyclesankey'
], function(d3)
{
  var Sankey = function(options){
    
    var divid = options.divid;
    var margin = {top: 1, right: 10, bottom: 6, left: 10};
    this.width = options.width;
    var height = options.height - margin.top - margin.bottom;
    var title = options.title;

    var formatNumber = d3.format(",.0f"),
        format = function(d) { return 'value: ' + formatNumber(d);},
        color = d3.scale.category20();
    
    this.render = function ( data ) {
      div = d3.select(divid);
      var bbox = div.node().getBoundingClientRect();
      var width = this.width || bbox.width;
      width = width - margin.left - margin.right;
    
      var sankey = d3.sankey()
          .nodeWidth(15)
          .nodePadding(10)
          .size([width, height]);
        
      var path = sankey.link();
    
      div.select("svg").remove();
      
      var svg = div.append("svg")
        .attr( "preserveAspectRatio", "xMinYMid meet" )
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom);
        
      var rootGraphic = svg.append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
          
      sankey.nodes(data.nodes)
        .links(data.links)
        .layout(32);
    
      var allgraphics = svg.append("g").attr("id", "node-and-link-container" );
    
      var link = allgraphics.append("g").attr("id", "link-container")
          .selectAll(".link")
          .data(data.links)
        .enter().append("path")
          .attr("class", function(d) { return (d.causesCycle ? "cycleLink" : "link") })
          .attr("d", path)
              .sort(function(a, b) { return b.dy - a.dy; })
          ;
    
      link.filter( function(d) { return !d.causesCycle} )
            .style("stroke-width", function(d) { return Math.max(1, d.dy); })
    
      link.append("title")
          .text(function(d) { return d.source.name + " -> " + d.target.name + "\n" + format(d.value); });
    
      var node = allgraphics.append("g").attr("id", "node-container")
          .selectAll(".node")
          .data(data.nodes)
        .enter().append("g")
          .attr("class", "node")
          .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
        .call(d3.behavior.drag()
          .origin(function(d) { return d; })
          .on("dragstart", function() { this.parentNode.appendChild(this); })
          .on("drag", dragmove));
    
      node.append("rect")
          .attr("height", function(d) { return d.dy; })
          .attr("width", sankey.nodeWidth())
          .style("fill", function(d) { return d.color = color(d.name.replace(/ .*/, "")); })
          .style("stroke", function(d) { return d3.rgb(d.color).darker(2); })
        .append("title")
          .text(function(d) { return d.name + "\n" + format(d.value); });
    
      node.append("text")
          .attr("x", -6)
          .attr("y", function(d) { return d.dy / 2; })
          .attr("dy", ".35em")
          .attr("text-anchor", "end")
          .attr("transform", null)
          .text(function(d) { return d.name; })
        .filter(function(d) { return d.x < width / 2; })
          .attr("x", 6 + sankey.nodeWidth())
          .attr("text-anchor", "start");
    
      function dragmove(d) {
        d3.select(this).attr("transform", "translate(" + d.x + "," + (d.y = Math.max(0, Math.min(height - d.dy, d3.event.y))) + ")");
        sankey.relayout();
        link.attr("d", path);
      }
    
      var numCycles = 0;
      for( var i = 0; i< sankey.links().length; i++ ) {
        if( sankey.links()[i].causesCycle ) {
          numCycles++;
        }
      }
    
      var cycleTopMarginSize = (sankey.cycleLaneDistFromFwdPaths() -
                ( (sankey.cycleLaneNarrowWidth() + sankey.cycleSmallWidthBuffer() ) * numCycles ) )
      var horizontalMarginSize = ( sankey.cycleDistFromNode() + sankey.cycleControlPointDist() );
      
      svg.append("text")
        .attr("x", (width / 2))             
        .attr("y", cycleTopMarginSize / 2 + margin.top)
        .attr("text-anchor", "middle")  
        .style("font-size", "16px") 
        .style("text-decoration", "underline")  
        .text(title);
    
      svg = d3.select(divid).select("svg")
        .attr( "viewBox",
              "" + (0 - horizontalMarginSize ) + " "         // left
              + cycleTopMarginSize + " "                     // top
              + (width + horizontalMarginSize * 2 ) + " "     // width
              + (height + (-1 * cycleTopMarginSize)) + " " );  // height
        
    };
  };
  return Sankey;
});