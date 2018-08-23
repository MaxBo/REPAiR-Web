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
            this.path = d3.geo.path().projection(transform);

            this.svg = d3.select(map.getPanes().overlayPane).append("svg");
            this.g = this.svg.append("g").attr("class", "leaflet-zoom-hide");

            // get zoom level after each zoom activity
            this.initialZoom = this.map.getZoom();
            // tooltip
            this.tooltip = d3.select("body")
                .append("div")
                .attr("class", "sankeymaptooltip")
                .style("opacity", 0.9);

            this.maxFlowWidth = 50;
            this.minFlowWidth = 2;
            this.maxScale = 2;

            this.map.on("zoomend", function(evt){ _this.resetView() });

            this.nodesData = {};
            this.flowsData = {};
        }

        // fit svg layer to map
        resetView(){
            var svgPos = this.resetBbox(),
                topLeft = svgPos[0];
            this.g.attr("transform",
                        "translate(" + -topLeft[0] + "," + -topLeft[1] + ") ");
            this.draw();
        }

        resetBbox(bbox){
            if (bbox) this.bbox = bbox;
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
            this.flowsData = {};
        }

        addNodes(nodes){
            var _this = this,
                // boundingbox
                topLeft = [10000, 0],
                bottomRight = [0, 10000];
            nodes.forEach(function(node){
                _this.nodesData[node.id] = node;
            })
            Object.values(_this.nodesData).forEach(function(node){
                topLeft = [Math.min(topLeft[0], node.lon), Math.max(topLeft[1], node.lat)];
                bottomRight = [Math.max(bottomRight[0], node.lon), Math.min(bottomRight[1], node.lat)];
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
            this.minFlowValue = Math.min(...totalValues);
        }

        draw() {
            this.g.selectAll("*").remove();
            // remember scope of 'this' as context for functions with different scope
            var _this = this,
                scale = Math.min(this.scale(), this.maxScale);

            // define data to use for drawPath and drawTotalPath as well as nodes data depending on flows
            for (var linkId in this.flowsData) {
                var combinedFlows = _this.flowsData[linkId],
                    totalValue = 0,
                    paths = [],
                    sxp, syp, txp, typ, sourceRadius, targetRadius;

                // ToDo: reenable "bothways" (meaning flows back and forth between two nodes)
                var bothways = false;

                combinedFlows.forEach(function(c){ totalValue += c.value });

                var totalStroke = _this.minFlowWidth + ((totalValue * scale) / _this.maxFlowValue * _this.maxFlowWidth),
                    offset = - totalStroke / 2;
                combinedFlows.forEach(function(flow){
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
                    var share = flow.value / totalValue,
                        strokeWidth = totalStroke * share;
                    offset += strokeWidth;

                    var sourceCoords = _this.projection([source['lon'], source['lat']]),
                        targetCoords = _this.projection([target['lon'], target['lat']]);

                    //add projection to source and target coordinates
                    sxp = sourceCoords[0];
                    syp = sourceCoords[1];
                    txp = targetCoords[0];
                    typ = targetCoords[1];

                    sourceRadius = source.radius * scale,
                    targetRadius = target.radius * scale;

                    var points = _this.getPointsFromPath(sxp, syp, txp, typ, strokeWidth, sourceRadius, targetRadius, offset, bothways),
                        path = _this.drawPath(points, flow.label, flow.color, strokeWidth);
                    paths.push(path);
                });
                if (paths.length === 0) continue;
                //  clip arrow head (take the last calculated points, same anyway for all combined flows)
                var points = _this.getPointsFromPath(sxp, syp, txp, typ, totalStroke, sourceRadius, targetRadius, totalStroke / 2, bothways),
                    clipPath = _this.drawArrowhead(points[0].x, points[0].y, points[1].x, points[1].y, targetRadius, totalStroke, linkId);
                paths.forEach(function(path){
                    path.attr("clip-path", clipPath);
                })
            };

            // use addpoint for each node in nodesDataFlow
            Object.values(_this.nodesData).forEach(function (node) {
                var x = _this.projection([node.lon, node.lat])[0],
                    y = _this.projection([node.lon, node.lat])[1],
                    radius = node.radius * scale / 2;
                _this.addPoint(x, y, node.label, node.innerLabel, node.color, radius);
            });
            this.setAnimation();
        }

        scale(){
            var zoomLevel = this.map.getZoom(),
                d = zoomLevel - this.initialZoom,
                scale = Math.pow(2, d);
            return scale;
        }

        //function to add source nodes to the map
        addPoint(x, y, label, innerLabel, color, radius) {
            var _this = this;

            var point = this.g.append("g").attr("class", "node");
            point.append("circle")
                 .attr("cx", x)
                 .attr("cy", y)
                 .attr("r", radius)
                 .style("fill", color)
                 .style("fill-opacity", 1)
                 .style("stroke", 'lightgrey')
                 .style("stroke-width", 1)
                 .on("mouseover", function (d) {
                     d3.select(this).style("cursor", "pointer");
                     _this.tooltip.transition()
                         .duration(200)
                         .style("opacity", 0.9);
                     _this.tooltip.html(label)
                         .style("left", (d3.event.pageX) + "px")
                         .style("top", (d3.event.pageY - 28) + "px")
                 })
                 .on("mouseout", function (d) {
                     _this.tooltip.transition()
                         .duration(500)
                         .style("opacity", 0)
                     }
                 );
            point.append("text")
                 .attr("x", x)
                 .attr("y", y + 5)
                 .attr("text-anchor", "middle")
                 .style("font-size", "14px")
                 .attr('fill','white')
                 .text(innerLabel || "");

        }

        // function to define line length adjustment
        adjustedPathLength(sxp, syp, txp, typ, sourceRadius, targetRadius) {
            var dxp = txp - sxp,
                dyp = typ - syp;
            var flowLength = Math.sqrt(dxp * dxp + dyp * dyp);
            var sourceReduction = sourceRadius,
                targetReduction = - targetRadius;

            // ratio between full line length and shortened line
            var sourceRatio = sourceReduction / flowLength,
                targetRatio = targetReduction / flowLength;

            // value by which line gets shorter
            var sxReductionValue = dxp * sourceRatio,
                syReductionValue = dyp * sourceRatio,
                txReductionValue = dxp * targetRatio,
                tyReductionValue = dyp * targetRatio;

            // source and target coordinates + projection + offset + adjusted length
            var sxpa = sxp + sxReductionValue,
                sypa = syp + syReductionValue,
                txpa = txp + txReductionValue,
                typa = typ + tyReductionValue;

            return [dxp, dyp, sxpa, sypa, txpa, typa, flowLength];
        }

        // function to calculate total offset for each flow by connection
        totalOffset(sxpa, sypa, txpa, typa, dxp, dyp, flowLength, offset, totalStroke, bothways){
            if (bothways) {
                var sxpao = sxpa + (offset) * (dyp / flowLength),
                    sypao = sypa - (offset) * (dxp / flowLength),
                    txpao = txpa + (offset) * (dyp / flowLength),
                    typao = typa - (offset) * (dxp / flowLength);
                return [sxpao, sypao, txpao, typao];
            }
            else {
                var sxpao = sxpa + (offset - (totalStroke / 2)) * (dyp / flowLength),
                    sypao = sypa - (offset - (totalStroke / 2)) * (dxp / flowLength),
                    txpao = txpa + (offset - (totalStroke / 2)) * (dyp / flowLength),
                    typao = typa - (offset - (totalStroke / 2)) * (dxp / flowLength);
                return [sxpao, sypao, txpao, typao];
            }
        }

        getPointsFromPath(sxp, syp, txp, typ, totalStroke, sourceRadius, targetRadius, offset, bothways){
            var pathLengthValues = this.adjustedPathLength(sxp, syp, txp, typ, sourceRadius, targetRadius);
            var dxp = pathLengthValues[0],
                dyp = pathLengthValues[1],
                sxpa = pathLengthValues[2],
                sypa = pathLengthValues[3],
                txpa = pathLengthValues[4],
                typa = pathLengthValues[5],
                flowLength = pathLengthValues[6];

            var totalOffset = this.totalOffset(sxpa, sypa, txpa, typa, dxp, dyp, flowLength, offset, totalStroke, bothways);
            var sxpao = totalOffset[0],
                sypao = totalOffset[1],
                txpao = totalOffset[2],
                typao = totalOffset[3];

            return [
                { x: sxpao, y: sypao },
                { x: txpao, y: typao }
            ];
        }

        defineTriangleData(sxpao, sypao, txpao, typao, targetRadius, totalStroke, flowLength, dxp, dyp){
            var triangleData = [];
            var tReduction = - targetRadius,
                tRatio = tReduction / flowLength,
                txRValue = dxp * tRatio,
                tyRValue = dyp * tRatio,
                sxpl = sxpao + (totalStroke / 2) * (dyp / flowLength),
                sypl = sypao - (totalStroke / 2) * (dxp / flowLength),
                txplb = (txpao + (totalStroke / 2) * (dyp / flowLength))+ txRValue*(totalStroke/5),
                typlb = (typao - (totalStroke / 2) * (dxp / flowLength))+ tyRValue*(totalStroke/5),
                sxpr = sxpao - (totalStroke / 2) * (dyp / flowLength),
                sypr = sypao + (totalStroke / 2) * (dxp / flowLength),
                txprb = (txpao - (totalStroke / 2) * (dyp / flowLength))+ txRValue*(totalStroke/5),
                typrb = (typao + (totalStroke / 2) * (dxp / flowLength))+ tyRValue*(totalStroke/5);
            triangleData.push({'tx': sxpl, 'ty': sypl}, {'tx': txplb, 'ty': typlb},
                {'tx': txpao, 'ty': typao},
                {'tx': txprb, 'ty': typrb}, {'tx': sxpr, 'ty': sypr});
            return triangleData;
        }

        // function to draw actual paths for the directed quantity flows
        drawPath(points, label, color, strokeWidth) {
            var _this = this;
            var line = d3.svg.line()
                         .x(function(d) { return d.x; })
                         .y(function(d) { return d.y; });
            var path = this.g.append("path")
                .attr('d', line(points))
                .attr("stroke-width", strokeWidth)
                .attr("stroke", color)
                .attr("stroke-opacity", 0.5)
                .style("pointer-events", 'all')
                .on("mouseover", function () {
                    d3.select(this).node().parentNode.appendChild(this);
                    d3.select(this).style("cursor", "pointer");
                    _this.tooltip.transition()
                            .duration(200)
                            .style("opacity", 0.8);
                    _this.tooltip.html(label)
                            .style("left", (d3.event.pageX) + "px")
                            .style("top", (d3.event.pageY - 28) + "px")
                    path.attr("stroke-opacity", 1)
                })
                .on("mouseout", function () {
                    _this.tooltip.transition()
                        .duration(500)
                        .style("opacity", 0)
                    path.attr("stroke-opacity", 0.5)
                });
            return path;
        }

        setAnimation(on){
            if(on != null) this.doAnimation = on;
            this.g.selectAll('path').classed('flowline', this.doAnimation);
        }

        // clip path-function to use on draw path to get arrowheads
        drawArrowhead(sxpao, sypao, txpao, typao, targetRadius, totalStroke, id){
            var dxp = txpao - sxpao,
                dyp = typao - sypao;
            var flowLength = Math.sqrt(dxp * dxp + dyp * dyp);
            var triangleData = this.defineTriangleData(sxpao, sypao, txpao, typao, targetRadius, totalStroke, flowLength, dxp, dyp);

            var clip = this.g.append("clipPath")
                .attr("id", "clip"+id)
                .append("polygon")
                .data(triangleData)
                .attr("points", triangleData.map(function (d) {
                        var x = d.tx,
                            y = d.ty;
                        return [x, y].join(",");
                    }).join(" ")
                );
            return "url(#clip" + id +")";
        }
    }
    return FlowMap;
});
