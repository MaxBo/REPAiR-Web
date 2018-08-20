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

            this.svg = d3.select(map.getPanes().overlayPane).append("svg"),
                this.g = this.svg.append("g").attr("class", "leaflet-zoom-hide");

            // get zoom level after each zoom activity
            this.relZoom = 10;
            map.on("zoomend", function(){

                var zoomLevel = map.getZoom(),
                    d = zoomLevel - _this.relZoom;
                _this.scale = Math.pow(2, d);
            });

            // tooltip
            this.tooltip = d3.select("body")
                .append("div")
                .attr("class", "sankeymaptooltip")
                .style("opacity", 0.9);

           this.maxFlowWidth = 50;
           this.minFlowWidth = 2;
        }


        reset(bbox){
            if (bbox) this.bbox = bbox;
            var topLeft = this.projection(this.bbox[0]),
                bottomRight = this.projection(this.bbox[1]);
            topLeft = [topLeft[0] - 250, topLeft[1] - 250];
            bottomRight = [bottomRight[0] + 250, bottomRight[1] + 250];
            this.svg.attr("width", bottomRight[0] - topLeft[0])
                .attr("height", bottomRight[1] - topLeft[1])
                .style("left", topLeft[0] + "px")
                .style("top", topLeft[1] + "px");
            this.g.attr("transform", "translate(" + -topLeft[0] + "," + -topLeft[1] + ")");
        }

        // remove all prev. drawn flows and nodes
        clear(){
            this.g.selectAll("*").remove();
        }

        render(nodes, flows) {
            this.clear();
            // remember scope of 'this' as context for functions with different scope
            var _this = this,
                nodesData = {},
                flowsData = {};

            //Define data from flowsData dependending on unique connections
            var strokeWidths = [],
                values = flows.map(function(flow){ return flow.value }),
                maxValue = Math.max(...values),
                minValue = Math.min(...values);
            nodes.forEach(function(node){
                nodesData[node.id] = node;
            })

            flows.forEach(function(flow){
                // collect flows with same target
            })

            // define data to use for drawPath and drawTotalPath as well as nodes data depending on flows
            flows.forEach(function(flow) {

                // define source and target by combining nodes and flows data --> flow has source and target that are connected to nodes by IDs
                // multiple flows belong to each node, storing source and target coordinates for each flow wouldn't be efficient
                var sourceId = flow.source,
                    source = nodesData[sourceId],
                    targetId = flow.target,
                    target = nodesData[targetId];
                // skip if there is no source or target for some data
                if (!source || !target) {
                    console.log('Warning: missing actor for flow');
                    return;
                }
                var width = _this.defineStrokeZoom(flow.value),
                    strokeWidth = _this.minFlowWidth + (width / maxValue * _this.maxFlowWidth);

                //var strokeWidth = _this.minFlowWidth + (width / maxValue * _this.maxFlowWidth);
                var sourceCoords = [source['lon'], source['lat']],
                    targetCoords = [target['lon'], target['lat']];

                //add projection to source and target coordinates
                var sxp = _this.projection(sourceCoords)[0],
                    syp = _this.projection(sourceCoords)[1],
                    txp = _this.projection(targetCoords)[0],
                    typ = _this.projection(targetCoords)[1];

                // drawTotalPath, if drawPath is chosen, every path is shown divided by materials which is not intended
                //if (_this.drawMaterials)

                // ToDo: enable "bothways" (meaning flows back and forth between two nodes)
                var bothways = false;

                var totalPoints = _this.getPointsFromTotalPath(sxp, syp, txp, typ, strokeWidth, source.level, target.level, bothways);
                var sxpao = totalPoints[0],
                    sypao = totalPoints[1],
                    txpao = totalPoints[2],
                    typao = totalPoints[3];

                var adjustedPathLength = _this.adjustedPathLength(sxp, syp, txp, typ, source.level, target.level);
                var dxp = adjustedPathLength[0],
                    dyp = adjustedPathLength[1],
                    flowLength = adjustedPathLength[6];

                var clipPath = _this.drawArrowhead(sxpao, sypao, txpao, typao, target.level, strokeWidth, flowLength, dxp, dyp, flow.id);
                var linePoints = [
                    { x: sxpao, y: sypao },
                    { x: txpao, y: typao }
                ];
                var path = _this.drawPath(linePoints, flow.label, flow.color, strokeWidth);

                path.attr("clip-path", clipPath);
               // this.drawPath(sxp, syp, txp, typ, flow.style, flow.label, offset, strokeWidth, totalStroke, sourceLevel, targetLevel, bothways, connection)

            });

            // use addpoint for each node in nodesDataFlow
            nodes.forEach(function (node) {
                var x = _this.projection([node.lon, node.lat])[0],
                    y = _this.projection([node.lon, node.lat])[1],
                    radius = _this.defineRadiusZoom(node.level)/2;

                _this.addPoint(x, y, node.label, node.color, radius);
            });

        }


        // load data asynchronously, define to execute it sumultaneously
        renderTopo(nodesData, flowsData) {
            var _this = this;
            function loaded(error) {
                _this.render(nodesData, flowsData);
            }
        }

        defineRadius(level){
            if (level === 10) return 11;
            if (level === 8) return 16;
            if (level === 6) return 21;
            if (level === 4) return 26;
            return 11;
        }

        // make adjustments if using other datasets
        defineRadiusZoom(level){
            var radius = this.defineRadius(level);
            return radius * this.scale;
        }

        // make adjustments if using other datasets
        defineStrokeZoom(stroke){
            return stroke * this.scale;
        }


        //function to add source nodes to the map
        addPoint(x, y, label, color, radius) {
            var _this = this;

            var point = this.g.append("g")
                .attr("class", "node")
                .append("circle")
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

        }

        // function to define line length adjustment
        adjustedPathLength(sxp, syp, txp, typ, sourceLevel, targetLevel) {
            var dxp = txp - sxp,
                dyp = typ - syp;
            // adjust source- & target- Level radius with the zoom level
            var sourceLevel = this.defineRadiusZoom(sourceLevel),
                targetLevel = this.defineRadiusZoom(targetLevel);
            var flowLength = Math.sqrt(dxp * dxp + dyp * dyp);
            var sourceReduction = sourceLevel,
                targetReduction = - targetLevel;

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

        getPointsFromTotalPath(sxp, syp, txp, typ, totalStroke, sourceLevel, targetLevel, bothways){
            var pathLengthValues = this.adjustedPathLength(sxp, syp, txp, typ, sourceLevel, targetLevel);
            var dxp = pathLengthValues[0],
                dyp = pathLengthValues[1],
                sxpa = pathLengthValues[2],
                sypa = pathLengthValues[3],
                txpa = pathLengthValues[4],
                typa = pathLengthValues[5],
                flowLength = pathLengthValues[6];

            var offset = totalStroke / 2;

            var totalOffset = this.totalOffset(sxpa, sypa, txpa, typa, dxp, dyp, flowLength, offset, totalStroke, bothways);
            var sxpao = totalOffset[0],
                sypao = totalOffset[1],
                txpao = totalOffset[2],
                typao = totalOffset[3];

            return [sxpao,sypao,txpao,typao];
        }

        defineTriangleData(sxpao, sypao, txpao, typao, targetLevel, totalStroke, flowLength, dxp, dyp){
            var triangleData = [];
            var tReduction = - this.defineRadius(targetLevel),
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
            console.log(points)
            var line = d3.svg.line()
                         .x(function(d) { return d.x; })
                         .y(function(d) { return d.y; });
            var path = this.g.append("path")
                .attr('d', line(points))
                .attr("stroke-width", strokeWidth)
                .attr("stroke", color)
                .attr("stroke-opacity", 0.5)
                .attr('class', 'flowline')
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

        //// function to draw path divided by materials
        //drawPath(sxp, syp, txp, typ, color, label, offset, strokeWidth, totalStroke, sourceLevel, targetLevel, bothways, connection) {

            //var pathLengthValues = this.adjustedPathLength(sxp, syp, txp, typ, sourceLevel, targetLevel);
            //var dxp = pathLengthValues[0],
                //dyp = pathLengthValues[1],
                //sxpa = pathLengthValues[2],
                //sypa = pathLengthValues[3],
                //txpa = pathLengthValues[4],
                //typa = pathLengthValues[5],
                //flowLength = pathLengthValues[6],
                //_this = this;

            ////unique id for each clip path is necessary
            //var uid = this.uuidv4();

            //var totalOffset = this.totalOffset(sxpa, sypa, txpa, typa, dxp, dyp, flowLength, offset, totalStroke, bothways, connection);
            //var sxpao = totalOffset[0],
                //sypao = totalOffset[1],
                //txpao = totalOffset[2],
                //typao = totalOffset[3];

            //var totalPoints = this.getPointsFromTotalPath(sxp, syp, txp, typ, totalStroke, sourceLevel, targetLevel, bothways, connection);
            //var sxpaot = totalPoints[0],
                //sypaot = totalPoints[1],
                //txpaot = totalPoints[2],
                //typaot = totalPoints[3];

            //var triangleDataf = this.defineTriangleData(sxpaot, sypaot, txpaot, typaot, targetLevel, totalStroke, flowLength, dxp, dyp);

            //this.drawArrowhead(sxpaot, sypaot, txpaot, typaot, targetLevel, totalStroke, flowLength, dxp, dyp, uid);

            //var flows = this.g.append("line")
                //.attr("class", "fraction")
                //.attr("x1", sxpao)
                //.attr("y1", sypao)
                //.attr("x2", txpao)
                //.attr("y2", typao)
                //.attr("stroke-width", strokeWidth)
                //.attr("stroke", color)
                //.attr("stroke-opacity", 0.8)
                //.attr("clip-path", "url(#clip" + uid +")")
                //.on("click", function(){
                    //d3.selectAll("line.fraction").remove();
                    //_this.tooltip.style("opacity", 0);
                //})
                //.on("mouseover", function(){
                    //d3.select(this).node().parentNode.appendChild(this);
                    //d3.select(this).style("cursor", "pointer"),
                        //_this.tooltip.transition()
                            //.duration(200)
                            //.style("opacity", 0.9);
                        //_this.tooltip.html(label)
                            //.style("left", (d3.event.pageX) + "px")
                            //.style("top", (d3.event.pageY - 28) + "px")
                        //flows.attr("stroke-opacity", 1)
                //})
                //.on("mouseout", function(d) {
                        //_this.tooltip.transition()
                            //.duration(500)
                            //.style("opacity", 0)
                        //flows.attr("stroke-opacity", 0.8)
                    //}
                //);
        //}

        // clip path-function to use on draw path to get arrowheads
        drawArrowhead(sxpao, sypao, txpao, typao, targetLevel, totalStroke, flowLength, dxp, dyp, id){
            var triangleData = this.defineTriangleData(sxpao, sypao, txpao, typao, targetLevel, totalStroke, flowLength, dxp, dyp);

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
