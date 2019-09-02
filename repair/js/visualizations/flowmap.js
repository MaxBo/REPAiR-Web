/*
*  Data Input that is needed to use the class FlowMap:
* Nodes:
* @param {object} nodesData
* @param {string} nodesData.name - Label for the tooltips
* @param {number} nodesData.lon - Longitude (first part of coordinates)
* @param {number} nodesData.lat - Latitude (second part of coordinates)
* @param {string} nodesData.label - Label for the tooltips
* @param {number} nodesData.style - Style ID for the color
* @param {number} nodesData.level - Level to use for the radius
*
* Flows:
* @param {object} flowsData
* @param {string} flowsData.id - ID for each flow
* @param {number} flowsData.source - flow origin needs id that is connected to coordinates of the Data for the nodes
* @param {number} flowsData.target - flow destination needs id that is connected to coordinates of the Data for the nodes
* @param {number} flowsData.value - value for the widths (for seperated flows)
* @param {number} flowsData.valueTotal -   total value for the widths
* @param {string} flowsData.label - Label for the tooltips (for seperated flows)
* @param {string} flowsData.labelTotal - Label for the tooltips
* @param {number} flowsData.style - Style ID for the color
*
* Styles:
* @param{object} styles
* @param{hex} styles.nodeColor - color for the nodes
* @param{number} styles.radius - radius for the node
* @param{hex} styles.color - color for the flows
*
*/


define([
    'd3', 'topojson', 'd3-queue', 'leaflet'
], function(d3, topojson, d3queue, L){

    class FlowMap {

        constructor(map, options) {
            var options = options || {};
            this.map = map;
            var _this = this;

            this.showNodes = options.showNodes || false;
            this.showFlows = options.showFlows || false;
            this.width = options.width || this.map.offsetWidth;
            this.bbox = options.bbox;
            this.height = options.height || this.width / 1.5;
            this.projection = function(coords) {
                var point = map.latLngToLayerPoint(new L.LatLng(coords[1], coords[0]));
                return [point.x, point.y];
            }

            function projectPoint(x, y) {
                var coords = _this.projection([x, y]);
                this.stream.point(point.x, point.y);
            }

            var transform = d3.geo.transform({point: projectPoint});
            this.overlay = map.getPanes().overlayPane;
            this.path = d3.geo.path().projection(transform);

            // tooltip
            this.tooltip = d3.select(this.overlay)
                .append("div")
                .attr("class", "sankeymaptooltip")
                .style("opacity", 0);

            this.svg = d3.select(this.overlay).append("svg");
            this.g = this.svg.append("g").attr("class", "leaflet-zoom-hide");

            // get zoom level after each zoom activity
            this.initialZoom = this.map.getZoom();
            this.maxFlowWidth = 50;
            this.minFlowWidth = 1;
            this.maxScale = 2;

            this.map.on("zoom", function(evt){
                _this.svg.node().style.visibility = 'hidden';
            });
            this.map.on("zoomend", function(evt){ _this.resetView() });

            this.nodesData = {};
            this.flowsData = {};
            this.nodesPos = {};
            this.hideTags = {};
        }

        // fit svg layer to map
        resetView(){

            this.svg.node().style.visibility = 'visible';
            var svgPos = this.resetBbox();
            if (!svgPos) return;
            var topLeft = svgPos[0];
            this.g.attr("transform",
                        "translate(" + -topLeft[0] + "," + -topLeft[1] + ") ");
            this.draw();
        }

        resetBbox(bbox){
            if (bbox) this.bbox = bbox;
            if (!this.bbox) return;
            var topLeft = this.projection(this.bbox[0]),
                bottomRight = this.projection(this.bbox[1]);
            topLeft = [topLeft[0] - 250, topLeft[1] - 250];
            bottomRight = [bottomRight[0] + 250, bottomRight[1] + 250];
            this.svg.attr("width", bottomRight[0] - topLeft[0])
                .attr("height", bottomRight[1] - topLeft[1])
                .style("left", topLeft[0] + "px")
                .style("top", topLeft[1] + "px");
            return [topLeft, bottomRight]
        }

        // remove all prev. drawn flows and nodes
        clear(){
            this.g.selectAll("*").remove();
            this.nodesData = {};
            this.nodesPos = {};
            this.flowsData = {};
            //this.hideTags = {};
        }

        addNodes(nodes){
            var _this = this,
                // boundingbox
                topLeft = [10000, 0],
                bottomRight = [0, 10000];
            nodes.forEach(function(node){
                // collect nodes with same position
                var pos = node.lat + '-' + node.lon;
                if (_this.nodesPos[pos] == null) _this.nodesPos[pos] = [];
                _this.nodesPos[pos].push(node);
                _this.nodesData[node.id] = node;
            })
            this.totalNodeValue = 0;
            Object.values(this.nodesData).forEach(function(node){
                topLeft = [Math.min(topLeft[0], node.lon), Math.max(topLeft[1], node.lat)];
                bottomRight = [Math.max(bottomRight[0], node.lon), Math.min(bottomRight[1], node.lat)];
                _this.totalNodeValue += node.value || 0;
            })
            this.maxNodeValue = 0;
            Object.values(this.nodesPos).forEach(function(nodes){
                nodes.forEach(function(node){
                    _this.maxNodeValue = Math.max(_this.maxNodeValue, node.value || 0);
                })
            })
            this.resetBbox([topLeft, bottomRight]);

        }

        zoomToFit(){
            if (!this.bbox) return;
            // leaflet uses lat/lon in different order
            this.map.fitBounds([
                [this.bbox[0][1], this.bbox[0][0]],
                [this.bbox[1][1], this.bbox[1][0]]
            ]);
        }

        addFlows(flows){
            var _this = this;
            flows.forEach(function(flow){
                // collect flows with same source and target
                var linkId = flow.source + '-' + flow.target;
                if (_this.flowsData[linkId] == null) _this.flowsData[linkId] = [];
                _this.flowsData[linkId].push(flow);
            })

            var totalValues = [];
            Object.values(this.flowsData).forEach(function(links){
                var totalValue = 0;
                links.forEach(function(c){ totalValue += c.value });
                totalValues.push(totalValue)
            })
            this.maxFlowValue = Math.max(...totalValues);
            //this.minFlowValue = Math.min(...totalValues);
        }

        draw() {
            this.g.selectAll("*").remove();
            // remember scope of 'this' as context for functions with different scope
            var _this = this,
                scale = Math.min(this.scale(), this.maxScale);

            // define data to use for drawPath and drawTotalPath as well as nodes data depending on flows
            for (var linkId in this.flowsData) {
                var combinedFlows = _this.flowsData[linkId],
                    shiftStep = 0.3 / combinedFlows.length,
                    xshift = 0.4,
                    yshift = 0.1,
                    curve = (combinedFlows.length > 1) ? 'arc' : 'bezier';

                combinedFlows.forEach(function(flow){
                    // flow is hidden -> ignore
                    if(_this.hideTags[flow.tag]) return;
                    // define source and target by combining nodes and flows data --> flow has source and target that are connected to nodes by IDs
                    // multiple flows belong to each node, storing source and target coordinates for each flow wouldn't be efficient
                    var sourceId = flow.source,
                        targetId = flow.target,
                        source = _this.nodesData[sourceId],
                        target = _this.nodesData[targetId];
                    // skip if there is no source or target for some data
                    if (!source || !target) {
                        console.log('Warning: missing actor for flow');
                        return;
                    }
                    // smaller dots for ainimation
                    var maxFlowWidth = (_this.animate && _this.dottedLines) ? 20 : _this.maxFlowWidth,
                        minFlowWidth = (_this.animate && _this.dottedLines) ? 2 : _this.minFlowWidth,
                        normFactor = maxFlowWidth / _this.maxFlowValue;

                    // this one is logarithmic but producing too many big lines
                    //var calcWidth = maxFlowWidth * Math.log2(1 + flow.value) / Math.log2(1 + _this.maxFlowValue),
                        //strokeWidth = Math.max(minFlowWidth, calcWidth);;

                    //var strokeWidth = Math.max(_this.minFlowWidth, (flow.value * scale) / _this.maxFlowValue * _this.maxFlowWidth );
                    var calcWidth = (flow.value) * normFactor,
                        strokeWidth = Math.max(minFlowWidth, calcWidth);

                    var sourceCoords = _this.projection([source['lon'], source['lat']]),
                        targetCoords = _this.projection([target['lon'], target['lat']]);

                    if(_this.animate){
                        var dash = {
                            length: 10,
                            gap: 4,
                            offset: 0
                        };
                        if (_this.dottedLines) {
                            var dashLength = 0,
                                dashGaps = strokeWidth * 3;
                            // the smaller the flow value the bigger the gaps
                            dashGaps += 50 - 50 * flow.value / _this.maxFlowValue;
                            var offset = Math.floor(Math.random() * dashGaps);
                            dash = {
                                length: dashLength,
                                gap: dashGaps,
                                offset: offset,
                                rounded: true
                            };
                        }
                    }
                    var options = {
                        xshift: xshift,
                        yshift: yshift,
                        animate: _this.animate,
                        dash: dash,
                        curve: curve
                    };
                    var coords = [
                        {x: sourceCoords[0], y: sourceCoords[1]},
                        {x: targetCoords[0], y: targetCoords[1]}
                    ];
                    var path = _this.drawPath(
                        coords, flow.label, flow.color, strokeWidth, options
                    );
                    // workaround for mouseover very thin lines
                    // put invisible line on top (with mouseover)
                    if (!_this.animate && strokeWidth < 7) {
                        options.opacity = 0;
                        var bufferedPath = _this.drawPath(
                            coords, flow.label, flow.color, 7, options
                        );
                    }

                    xshift -= shiftStep;
                    yshift += shiftStep;
                });
            };

            function calcRadius(value){
                return 5 + 50 * Math.pow(value / _this.totalNodeValue, 0.5);
            }
            var maxNodeRadius = calcRadius(this.maxNodeValue);
            var scaleFactor = (maxNodeRadius > 60) ? 60 / maxNodeRadius  : 1
            // use addpoint for each node in nodesDataFlow
            Object.values(_this.nodesPos).forEach(function (nodes) {

                // ignore hidden nodes
                var nodesToShow = [];
                nodes.forEach(function(node){
                    if(!_this.hideTags[node.tag]) nodesToShow.push(node);
                })
                // no visible nodes
                if (nodesToShow.length === 0) return;

                var first = nodesToShow[0];
                var x = _this.projection([first.lon, first.lat])[0],
                    y = _this.projection([first.lon, first.lat])[1];
                // only one node at this position
                if (nodesToShow.length === 1){
                    if(_this.hideTags[first.tag]) return;
                    // calculate radius by value, if radius is not given
                    var radius = Math.max(5, first.radius || calcRadius(first.value));
                    _this.addPoint(x, y, first.label, first.innerLabel, first.color, radius, first.opacity);
                }
                // multiple nodes at same position -> piechart
                else {
                    var data = [], label = '',
                        radius = 0,
                        total = 0;
                    nodesToShow.forEach(function(node){
                        total += node.value;
                        radius += node.radius || 0;
                        label += node.label + '<br><br>';
                        data.push({
                            'color': node.color,
                            'value': node.value || 1,
                            'opacity': node.opacity
                        })
                    })
                    radius = Math.max(5, (radius + calcRadius(total)) * scaleFactor);
                    _this.addPieChart(x, y, label, radius, data)
                }
            });
        }

        scale(){
            var zoomLevel = this.map.getZoom(),
                d = zoomLevel - this.initialZoom,
                scale = Math.pow(2, d);
            return scale;
        }

        // draw pie chart at given position
        addPieChart(x, y, label, radius, data) {
            var _this = this;

            var pie = d3.layout.pie().value(function(d) { return d.value; });

            var arc = d3.svg.arc()
                .outerRadius(radius)
                .innerRadius(0);
            var point = this.g.append("g").attr("class", "node")
                .attr("transform","translate("+x+"," + y+")");
            var arcs = point.selectAll(".arc")
                .data(pie(data))
                .enter().append("g")
                .attr("class", "arc")
            //var arcg = selection.attr("transform","translate("+x+"," + y+")")
                    //.selectAll(".arc")
                    //.data(pie(d.children))
                    //.enter().append("g")
                    //.attr("class", "arc");
            arcs.append("path")
                .attr("d", arc)
                .style("fill", function(d, i) {
                    return d.data.color;
                })
                //.style("fill-opacity", function(d, i) {
                    //return d.data.opacity || 1;
                //})
                .style("stroke", 'lightgrey')
                .style("stroke-width", 1)
                .style("pointer-events", 'all')
                .on("mouseover", function (d) {
                    d3.select(this).style("cursor", "pointer");
                    var rect = _this.overlay.getBoundingClientRect();
                    _this.tooltip.transition()
                        .duration(200)
                        .style("opacity", 0.9);
                    _this.tooltip.html(label)
                        .style("left", (d3.event.pageX - rect.x - window.pageXOffset) + "px")
                        .style("top", (d3.event.pageY - rect.y - 28 - window.pageYOffset) + "px")
                    //d3.select(this).style("fill-opacity", 1);
                })
                .on("mouseout", function (d) {
                    _this.tooltip.transition()
                        .duration(500)
                        .style("opacity", 0)
                    //d3.select(this).style("fill-opacity", d.data.opacity || 1);
                });
        }

        //function to add source nodes to the map
        addPoint(x, y, label, innerLabel, color, radius, opacity) {
            var _this = this;

            var point = this.g.append("g").attr("class", "node");
            point.append("circle")
                 .attr("cx", x)
                 .attr("cy", y)
                 .attr("r", radius)
                 .style("fill", color)
                 .style("fill-opacity", opacity || 1)
                 .style("stroke", 'lightgrey')
                 .style("stroke-width", 1)
                 .on("mouseover", function (d) {
                     d3.select(this).style("cursor", "pointer");
                     var rect = _this.overlay.getBoundingClientRect();
                     _this.tooltip.transition()
                         .duration(200)
                         .style("opacity", 0.9);
                     _this.tooltip.html(label)
                         .style("left", (d3.event.pageX - rect.x - window.pageXOffset) + "px")
                         .style("top", (d3.event.pageY - rect.y - 28 - window.pageYOffset) + "px");
                     d3.select(this).style("fill-opacity", 1);
                 })
                 .on("mouseout", function (d) {
                    _this.tooltip.transition()
                        .duration(500)
                        .style("opacity", 0)
                    d3.select(this).style("fill-opacity", opacity);
                 });
            point.append("text")
                 .attr("x", x)
                 .attr("y", y + 5)
                 .attr("text-anchor", "middle")
                 .style("font-size", "14px")
                 .attr('fill','white')
                 .text(innerLabel || "");
        }

        // function to draw actual paths for the directed quantity flows
        drawPath(points, label, color, strokeWidth, options ) {
            var _this = this,
                options = options || {};
            var line = d3.svg.line()
                         .x(function(d) { return d.x; })
                         .y(function(d) { return d.y; });
            // Determine control point locations for different link styles
            var bezier = function(points) {
                // Set control point inputs
                var source = points[0],
                    target = points[1],
                    dx = source.x - target.x,
                    dy = source.y - target.y,
                    sx = options.xshift || 0.4,
                    sy = options.yshift || 0.1;
                //bezier or arc
                var controls = (options.curve === 'arc') ? [sx*dx, sy*dy, sy*dx, sx*dy] : [sx*dx, sy*dy, sx*dx, sy*dy];

                return "M" + source.x + "," + source.y
                     + "C" + (source.x - controls[0]) + "," + (source.y - controls[1])
                     + " " + (target.x + controls[2]) + "," + (target.y + controls[3])
                     + " " + target.x + "," + target.y;
            };
            var opacity = (options.opacity != null) ? options.opacity : 0.5;
            var path = this.g.append("path")
                .attr('d', bezier(points))
                .attr("stroke-width", strokeWidth)
                .attr("stroke", color)
                .attr("fill", 'none')
                .attr("stroke-opacity", opacity)
                .attr("stroke-linecap", (!options.animate || (options.dash && options.dash.rounded)) ? "round": "unset")
                .style("pointer-events", (options.animate && (options.dash && options.dash.rounded)) ? 'none' : 'stroke')
                .on("mouseover", function () {
                    d3.select(this).node().parentNode.appendChild(this);
                    d3.select(this).style("cursor", "pointer");
                     var rect = _this.overlay.getBoundingClientRect();
                    _this.tooltip.transition()
                        .duration(200)
                        .style("opacity", 0.8);
                    _this.tooltip.html(label)
                         .style("left", (d3.event.pageX - rect.x - window.pageXOffset) + "px")
                         .style("top", (d3.event.pageY - rect.y - 28 - window.pageYOffset) + "px")
                    path.attr("stroke-opacity", 1)
                })
                .on("mouseout", function () {
                    _this.tooltip.transition()
                        .duration(500)
                        .style("opacity", 0)
                    path.attr("stroke-opacity", opacity)
                })
                .classed('flow', true)
                .classed('animated', options.animate);
            if (options.dash){
                var dash = options.dash;
                path.attr("stroke-dasharray", [dash.length, dash.gap].join(','));
                path.attr("stroke-dashoffset", dash.offset);
            }
            return path;
        }

        toggleAnimation(on){
            if(on != null) this.animate = on;
            //this.g.selectAll('path').classed('flowline', this.animate);
            this.draw();
        }

        toggleTag(tag, on){
            this.hideTags[tag] = !on;
        }

    }
    return FlowMap;
});
