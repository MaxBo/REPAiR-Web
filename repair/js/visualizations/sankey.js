define(['d3', 'd3-tip', 'utils/utils', 'cyclesankey'],
function(d3, d3tip, utils) {
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
    * @param {string} [options.language='en-US'] language code
    * @param {Boolean} options.gradient render links as gradients from source.color to target.color, else render in source.color only
    *
    */
    constructor(options){
        this.el = options.el;
        this.margin = { top: 1, right: 10, bottom: 6, left: 10 };
        this.height = options.height - this.margin.top - this.margin.bottom;
        this.title = options.title;

        this.div = d3.select(this.el);
        this.bbox = this.div.node().getBoundingClientRect();
        this.width = options.width || this.width;
        this.width = this.width - this.margin.left - this.margin.right;
        this.language = options.language || 'en-US';
        this.sankey = d3.sankey()
            .nodeWidth(15)
            .nodePadding(10)
            .size([this.width, this.height]);
        this.selectable = options.selectable;
        this.gradient = options.gradient;
    }

    format(d) {
        return d.toLocaleString(this.language);
    }

    setSize(width, height) {
        this.width = width - this.margin.left - this.margin.right;
        this.height = height;
        this.svg.attr("width", width)
                .attr("height", height);
    }

    zoomToFit(duration) {
        var size = this.sankey.size(),
            ratio = this.width / size[0],
            scale = ratio * 0.8,
            duration = duration || 0,
            g = this.svg.select('g');
        g.transition().duration(duration).call(this.zoom.translate([50,10]).scale(scale).event);
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
        this.zoom = {};
        var drag = {};
        var g = {};
        d3.selectAll("a[data-zoom]").on("click", clicked);
        function clicked() {
            var valueZoom = this.getAttribute("data-zoom");
            if (valueZoom != 0)
            {
                g.call(_this.zoom);
                // Record the coordinates (in data space) of the center (in screen space).
                var center0 = _this.zoom.center(),
                    translate0 = _this.zoom.translate(),
                    coordinates0 = coordinates(center0);
                _this.zoom.scale(_this.zoom.scale() * Math.pow(2, +valueZoom));

                // Translate back to the center.
                var center1 = point(coordinates0);
                _this.zoom.translate([translate0[0] + center0[0] - center1[0], translate0[1] + center0[1] - center1[1]]);

                g.transition().duration(750).call(_this.zoom.event);
            } else {
                _this.zoomToFit(500);
            }
        }

        function coordinates(point) {
            var scale = _this.zoom.scale(),
                translate = _this.zoom.translate();
            return [(point[0] - translate[0]) / scale, (point[1] - translate[1]) / scale];
        }

        function point(coordinates) {
            var scale = _this.zoom.scale(),
                translate = _this.zoom.translate();
            return [coordinates[0] * scale + translate[0], coordinates[1] * scale + translate[1]];
        }

        var path = this.sankey.link();

        // remove old svg if it was already rendered
        this.div.select("svg").remove();
        $(".d3-tip").remove();

        /* Initialize tooltip */
        var tipLinks = d3tip()
            .attr('class', 'd3-tip d3-tip-links')
            .offset([-10,0]);

        var tipNodes = d3tip()
            .attr('class', 'd3-tip d3-tip-nodes')
            .offset([-10, 0]);
        var linkTooltipOffset = 62,
            nodeTooltipOffset = 130;

        tipLinks.html(function(d) {
            var title = d.source.name + " -> " + d.target.name,
                value = _this.format(d.value) + " " + (d.units || "");
            return "<h1>" + title + "</h1>" + "<br>" + value + "<br><br>" + d.text;
        });

        tipNodes.html(function(d) {
            var inSum = 0,
                outSum = 0;
            var inUnits, outUnits;
            for (var i = 0; i < d.targetLinks.length; i++) {
                var link = d.targetLinks[i];
                inSum += link.value;
                if (!inUnits) inUnits = link.units; // in fact take first occuring unit, ToDo: can there be different units in the future?
            }
            for (var i = 0; i < d.sourceLinks.length; i++) {
                var link = d.sourceLinks[i];
                outSum += link.value;
                if (!outUnits) outUnits = link.units;
            }
            var ins = "in: " + _this.format(inSum) + " " + (inUnits || ""),
                out = "out: " + _this.format(outSum) + " " + (outUnits || "");
            var text = (d.text) ? d.text + '<br>': '';
            return "<h1>" + d.name + "</h1>" + text + "<br>" + ins + "<br>" + out;
        });

        function dragstarted(d) {
            d3.select(this).classed("dragging", true);
        }

        function dragged(d) {
            d3.select(this).attr("cx", d.x = d3.event.x).attr("cy", d.y = d3.event.y);
        }

        function dragended(d) {
            d3.select(this).classed("dragging", false);
        }

        drag = d3.behavior.drag()
        .origin(function(d) { return d; })
        .on("dragstart", dragstarted)
        .on("drag", dragged)
        .on("dragend", dragended);

        this.zoom = d3.behavior.zoom()
                          .scaleExtent([0, 5])
                          .center([this.width / 2, this.height / 2])
                          .on("zoom", zoomed);

        this.svg = this.div.append("svg")
            //.attr( "preserveAspectRatio", "xMinYMid meet" )
            .attr("width", this.width)
            .attr("height", this.height)
            .call(this.zoom)
            .call(tipLinks)
            .call(tipNodes)

        g = this.svg.append("g")
                    .attr("transform", "translate(" + this.margin.left + "," + this.margin.top + ")");

        // filter for text background
        var defs = g.append("defs");
        var filter = defs.append("filter")
            .attr("id", "text-bg")
            .attr("width", "1")
            .attr("height", "1")
            .attr("x", "0")
            .attr("y", "0");
        filter.append("feFlood")
            .attr("flood-opacity", "0.8")
            .attr("flood-color", "white");
        filter.append("feComposite")
            .attr("in", "SourceGraphic");

        this.sankey.nodes(data.nodes)
            .links(data.links)
            .layout({ iterations: 32, adjustSize: true });

        function strokeColor(d){
            if (_this.gradient && !d.isStock) {
                var gradientId = d.id + "-linear-gradient",
                    linearGradient = g.append("defs")
                    .append("linearGradient")
                    .attr("id", gradientId);
                linearGradient.append("stop")
                    .attr("offset", "0%")
                    .attr("stop-color", d.source.color);
                linearGradient.append("stop")
                    .attr("offset", "100%")
                    .attr("stop-color", d.target.color);
                return "url(#" + gradientId + ")";
            }
            return d.source.color || '#000';
        }

        var link = g.append("g").attr("class", "link-container")
            .selectAll(".link")
            .data(data.links)
        .enter().append("path")
            .attr("class", function(d) { return (d.causesCycle ? "cycleLink" : "link") })
            .attr("d", path)
            .sort(function(a, b) { return b.dy - a.dy; })
            .style("stroke", strokeColor)
            .style("fill", function(d){ return (d.causesCycle ? d.source.color : "none") })
            .on('mousemove', function(event) {
                tipLinks
                    .style("top", function() {
                        var top = d3.event.pageY - $('.d3-tip-links').height() / 2;
                        return top + "px";
                    })
                    .style("left", function () {
                        var left = d3.event.pageX + 20;
                        return left + "px"; })
                    .style("pointer-events", 'none')
                })
            .on('mouseover', function(d) { tipLinks.show(d, this); })
            .on('mouseout', function(d) { tipLinks.hide(d, this); })
            .on('click', function(d){
                if (_this.selectable){
                    var link = d3.select(this),
                        selected = link.classed("selected");
                    link.classed("selected", !selected);
                    var etype = (selected) ? 'linkDeselected': 'linkSelected',
                        event = new CustomEvent(etype, { detail: d });
                    _this.el.dispatchEvent(event);
                }
            })

        link.filter( function(d) { return !d.causesCycle} )
            .style("stroke-width", function(d) { return Math.max(1, d.dy); });

        var node = g.append("g").attr("class", "node-container")
            .selectAll(".node")
            .data(data.nodes)
        .enter().append("g")
            .attr("class", "node")
            .attr("transform", function(d) {
                return "translate(" + d.x + "," + d.y + ")";
            })
            .on('mousemove', function(event) {
                tipNodes
                    .style("top", d3.event.pageY - $('.d3-tip-nodes').height() / 2 + "px")
                    .style("left", function () {
                        var left = d3.event.pageX + 20;
                        return left + "px"; })
                    .style("pointer-events", 'none')
                })
            .on('mouseover', function(d) { tipNodes.show(d, this); })
            .on('mouseout', function(d) { tipNodes.hide(d, this); })
        .call(d3.behavior.drag()
            .origin(function(d) { return d; })
            .on("dragstart", function() {
                d3.event.sourceEvent.stopPropagation();  //Disable drag sankey on node select
                this.parentNode.appendChild(this); })
            .on("drag", dragmove))
        .call(alignToSource);

        var nodeWidth = this.sankey.nodeWidth();
        node.append("rect")
            .attr("height", function(d) { return d.dy; }) //Math.max(d.dy, 3); })
            .attr("width", nodeWidth)
            .style("fill", function(d) {
                if (d.color == undefined)
                    return d.color = utils.colorByName(d.name); //get new color if node.color is null
                return d.color;
            })
            .style("stroke", function(d) { return d3.rgb(d.color).darker(2); });

        // scale the font depending on zoom
        var fontRange = d3.scale.linear().domain([0, 0.5, 1, 4, 10]).range([50, 20, 16, 3, 2.5]);
        var rectRange = d3.scale.linear().domain([0, 0.5, 1, 5]).range([nodeWidth * 5, nodeWidth * 2, nodeWidth, nodeWidth]);
        function scaleFont(){ return fontRange(_this.zoom.scale()) + "px"; }
        function scaleRectWidth(){ return rectRange(_this.zoom.scale()); }

        node.append("text")
           // .style("filter", "url(#text-bg)")
            .attr("x", -6)
            .attr("y", function(d) { return d.dy / 2; })
            .attr("dy", ".35em")
            .attr("text-anchor", "end")
            .attr("transform", null)
            .text(function(d) { return d.name; })
            .filter(function(d) { return d.x < _this.width / 2; })
            .attr("x", 6 + this.sankey.nodeWidth())
            .attr("text-anchor", "start")
            .style("font-size", scaleFont);

        function zoomed() {
            var scale = d3.event.scale;
            node.selectAll('text').style("font-size", scaleFont);
            node.selectAll('rect').attr("width", scaleRectWidth);
            g.attr("transform", "translate(" + d3.event.translate + ")scale(" + scale + ")");
        }
        function dragmove(d) {
            d3.select(this).attr("transform",
                "translate(" + (
                    d.x = Math.max(0, d3.event.x)
                ) + "," + (
                    d.y = Math.max(0, d3.event.y)
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

        this.zoomToFit();

    };
};
return Sankey;
});
