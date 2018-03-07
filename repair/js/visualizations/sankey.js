define(['d3', 'libs/cycle-sankey'], function(d3) {
    /**
    *
    * sankey diagram of nodes and links between those nodes, supports cycles
    *
    * @author Christoph Franke
    */
    class Sankey{
    
        /**
        *
        * set up the sankey diagram
        *
        * @param {Object} options
        * @param {string} options.el        the HTMLElement to render the sankey diagram in
        * @param {string=} options.title    title of the diagram (displayed on top)
        * @param {string=} options.width    width of the diagram, defaults to bounding box of el
        * 
        */
        constructor(options){
            this.el = options.el;
            this.margin = {top: 1, right: 10, bottom: 6, left: 10};
            this.height = options.height - this.margin.top - this.margin.bottom;
            this.title = options.title;
            this.formatNumber = d3.format(",.0f"),
            this.color = d3.scale.category20();
            
            this.div = d3.select(this.el);
            var bbox = this.div.node().getBoundingClientRect();
            this.width = options.width || bbox.width;
            this.width = this.width - this.margin.left - this.margin.right;
    
            this.sankey = d3.sankey()
                .nodeWidth(15)
                .nodePadding(10)
                .size([this.width, this.height]);
        }
        
        format(d) {
            return d3.format(",.0f")(d);
        }
    
        /**
        * object describing a node
        * 
        * @typedef {Object} Sankey~Nodes
        * @property {string} id                    - unique id
        * @property {string} name                  - name to be displayed
        * @property {Object=} alignToSource        - align a node to the source of the first link going into this node
        * @property {number} [alignToSource.x = 0] - x offset to position of source
        * @property {number} [alignToSource.y = 0] - y offset to position of source
        */
    
        /**
        * object describing a link between two nodes
        * 
        * @typedef {Object} Sankey~Links
        * @property {number} source - index of source-node
        * @property {string} target - index of target-node
        * @property {number} value  - determines thickness of visualized link, also shown on mouseover/click
        * @property {string} text   - an additional text to be displayed on mouseover/click
        */
    
        /**
        * render the data
        *
        * @param {Array.<Sankey~Nodes>} nodes - array of nodes
        * @param {Array.<Sankey~Links>} links - array of links, origin and target indices refer to order of nodes
        */
        render( data ) {
    
            //sankey.nodeAlign(d3.sankeyLeft)
            var _this = this;
    
            var path = this.sankey.link();
    
            this.div.select("svg").remove();
    
            var svg = this.div.append("svg")
                .attr( "preserveAspectRatio", "xMinYMid meet" )
                .attr("width", this.width + this.margin.left + this.margin.right)
                .attr("height", this.height + this.margin.top + this.margin.bottom);
    
            var rootGraphic = svg.append("g")
                .attr("transform", "translate(" + this.margin.left + "," + this.margin.top + ")");
    
            this.sankey.nodes(data.nodes)
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
                .text(function(d) { return d.source.name + " -> " + d.target.name + "\n" + _this.format(d.value) + " " + (d.units || "") + "\n" + d.text; });
    
            var node = allgraphics.append("g").attr("id", "node-container")
                .selectAll(".node")
                .data(data.nodes)
            .enter().append("g")
                .attr("class", "node")
                .attr("transform", function(d) { 
                    return "translate(" + d.x + "," + d.y + ")"; 
                })
            .call(d3.behavior.drag()
                .origin(function(d) { return d; })
                .on("dragstart", function() { this.parentNode.appendChild(this); })
                .on("drag", dragmove))
            .call(alignToSource);
    
            node.append("rect")
                .attr("height", function(d) { return d.dy; })
                .attr("width", this.sankey.nodeWidth())
                .style("fill", function(d) { return d.color = _this.color(d.name.replace(/ .*/, "")); })
                .style("stroke", function(d) { return d3.rgb(d.color).darker(2); })
            .append("title")
                .text(function(d) { 
                    var inSum = 0,
                        outSum = 0;
                    for (var i = 0; i < d.targetLinks.length; i++) {
                        inSum += d.targetLinks[i].value; }
                    for (var i = 0; i < d.sourceLinks.length; i++) {
                        outSum += d.sourceLinks[i].value; }
                    return d.name + "\nin: " + inSum + "\nout: " + outSum; 
                });
    
            node.append("text")
                .attr("x", -6)
                .attr("y", function(d) { return d.dy / 2; })
                .attr("dy", ".35em")
                .attr("text-anchor", "end")
                .attr("transform", null)
                .text(function(d) { return d.name; })
            .filter(function(d) { return d.x < _this.width / 2; })
                .attr("x", 6 + this.sankey.nodeWidth())
                .attr("text-anchor", "start");
    
            //function dragmove(d) {
                //d3.select(this).attr("transform", "translate(" + d.x + "," + (d.y = Math.max(0, Math.min(height - d.dy, d3.event.y))) + ")");
                //sankey.relayout();
                //link.attr("d", path);
            //}
            function dragmove(d) {
                d3.select(this).attr("transform", 
                    "translate(" + (
                        d.x = Math.max(0, Math.min(_this.width - d.dx, d3.event.x))
                    ) + "," + (
                        d.y = Math.max(0, Math.min(_this.height - d.dy, d3.event.y))
                    ) + ")");
                _this.sankey.relayout();
                link.attr("d", path);
            }
    
            // align the node to it's source if requested
            function alignToSource() {
                var gNodes = d3.selectAll("g.node");
    
                for (var j = 0; j < data.nodes.length; j++) {
                    var node = data.nodes[j];
                    if (node.alignToSource != null){
                        var targetLink = node.targetLinks[0];
                        var source = targetLink.source;
                        var offsetX = node.alignToSource.x || 0,
                            offsetY = node.alignToSource.y || 0;
                        node.x = source.x + offsetX;
                        node.y = source.y + targetLink.sy + offsetY;
                        var gNode = gNodes[0][j];
                        d3.select(gNode).attr("transform", 
                            "translate(" + node.x + "," + node.y + ")");
                    }
                }
                _this.sankey.relayout();
                link.attr("d", path);
            }
    
            var numCycles = 0;
            for( var i = 0; i< this.sankey.links().length; i++ ) {
                if( this.sankey.links()[i].causesCycle ) {
                    numCycles++;
                }
            }
    
            var cycleTopMarginSize = (this.sankey.cycleLaneDistFromFwdPaths() -
                ( (this.sankey.cycleLaneNarrowWidth() + this.sankey.cycleSmallWidthBuffer() ) * numCycles ) )
            var horizontalMarginSize = ( this.sankey.cycleDistFromNode() + this.sankey.cycleControlPointDist() );
    
            svg.append("text")
                .attr("x", (this.width / 2))             
                .attr("y", cycleTopMarginSize / 2 + this.margin.top)
                .attr("text-anchor", "middle")  
                .style("font-size", "16px") 
                .style("text-decoration", "underline")  
                .text(this.title);
    
            svg = d3.select(this.el).select("svg")
                .attr( "viewBox",
                    "" + (0 - horizontalMarginSize ) + " "         // left
                    + cycleTopMarginSize + " "                     // top
                    + (this.width + horizontalMarginSize * 2 ) + " "     // width
                    + (this.height + (-1 * cycleTopMarginSize)) + " " );  // height
    
        };
    };
    return Sankey;
});