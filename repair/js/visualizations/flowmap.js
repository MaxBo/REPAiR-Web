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
            map.on("zoomend", function(){
                var zoomLev = map.getZoom();
            });
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

        render(nodesData, flowsData) {
            this.g.selectAll("*").remove();
            // remember scope of 'this' as context for functions with different scope
            var _this = this;


            //Define data from flowsData dependending on unique connections
            var strokeWidthPerFlow = {};
            var connections = [];
            var strokeWidthArrayPerConnection = {};
            var connectionSourceTarget = {};

            for (var key in flowsData) {
                var source = flowsData[key].source,
                    target = flowsData[key].target;

                var connection = source + '-' + target;
                //if connection not in Array connections: push
                if (connections.includes(connection) === false) {
                    connections.push(connection)
                    connectionSourceTarget [key] = {'connection': connection, 'source': source, 'target': target};
                    // get the strokeWidths for each flow that belongs to individual connections
                    var strokeWidths = {};
                    var strokeArray = [];
                    var maxValue = Math.max.apply(Math, Object.values(flowsData).map(function (flow) {
                            return flow.valueTotal
                        })),
                        minValue = Math.min.apply(Math, Object.values(flowsData).map(function (flow) {
                        return flow.valueTotal
                    })),
                        maxWidth = 5,
                        minWidth = 0.5;

                    for (var key in flowsData) {
                        var flow = flowsData[key];
                        if (flow.source + '-' + flow.target === connection) {
                            var width = flow.value;
                            // insert the zoom here, because thats where the actual width
                            var width = this.defineStrokeZoom(width);
                            var strokeWidth = minWidth + (width / maxValue * maxWidth);

                            strokeWidths[key] = strokeWidth;
                            strokeArray.push(strokeWidth)
                        }
                    }
                    strokeWidthArrayPerConnection[connection] = strokeArray;
                    //make items array to sort the values
                    var strokeWidthsArray = Object.keys(strokeWidths).map(function (key) {
                        return [key, strokeWidths[key]];
                    });
                    strokeWidthsArray.sort(function (first, second) {
                        return second[1] - first[1];
                    });

                    // define stroke widths for each connection sorted in an array
                    for (var i = 0; i < strokeWidthsArray.length; i++) {
                        var key = strokeWidthsArray[i][0];
                        var strokeWidth = strokeWidthsArray[i][1];
                        if (i === 0) {
                            var offset = strokeWidth / 2;
                        }
                        else {
                            var offset = strokeWidth / 2;
                            for (var j = 0; j < i; j++) {
                                offset = (offset + strokeWidthsArray[j][1])
                            }
                        }
                        strokeWidthPerFlow[key] = [strokeWidth, offset];
                    }
                }
            }
            // get all connections between two nodes that have flows in both directions
            var bothways = [];
            for (var key in connectionSourceTarget) {
                var source = connectionSourceTarget[key].source,
                    target = connectionSourceTarget[key].target;

                for (var con in connectionSourceTarget) {
                    var conSource = connectionSourceTarget[con].source,
                        conTarget = connectionSourceTarget[con].target;
                    if (source === conTarget && target === conSource) {
                        bothways.push(connectionSourceTarget[key].connection)
                    }
                }
            }


            // get the sum of all individual strokeWidths per same source & target
            var totalStrokeWidths = {};
            for (var key in strokeWidthArrayPerConnection) {
                var eachArray = strokeWidthArrayPerConnection[key],
                    totalStrokeWidthPerArray = 0;
                for (var i in eachArray) {
                    totalStrokeWidthPerArray += eachArray[i];
                }

                totalStrokeWidths[key] = totalStrokeWidthPerArray;
            }



            // define data to use for drawPath and drawTotalPath as well as nodes data depending on flows
            var nodesDataFlow = {};
            for (var key in flowsData) {
                // define flow, so that the loop doesn't have to start over and over again
                var flow = flowsData[key];
                // define source and target by combining nodes and flows data --> flow has source and target that are connected to nodes by IDs
                // multiple flows belong to each node, storing source and target coordinates for each flow wouldn't be efficient
                var sourceId = flow.source,
                    source = nodesData[sourceId],
                    targetId = flow.target,
                    target = nodesData[targetId];
                // insert a continue command to run through the data even if there is no source or target for some data
                if (!source || !target) {
                    console.log('Warning: missing actor for flow');
                    continue;
                }
                var sourceCoords = [source['lon'], source['lat']],
                    targetCoords = [target['lon'], target['lat']];

                //add projection to source and target coordinates
                var sxp = this.projection(sourceCoords)[0],
                    syp = this.projection(sourceCoords)[1],
                    txp = this.projection(targetCoords)[0],
                    typ = this.projection(targetCoords)[1];

                // define further adjustments for the paths: width, offset ( to see each material fraction even if they have same coordinates)
                var strokeWidth = strokeWidthPerFlow[key][0],
                    offset = strokeWidthPerFlow[key][1];
                // get the connection (persists of source+target) from this flow data; get the totalStrokeWidths for each connection
                var connection = sourceId + '-' + targetId,
                    totalStroke = totalStrokeWidths[connection];

                var sourceLevel = source.level,
                    targetLevel = target.level;

                var Bthis = this;

                nodesDataFlow[sourceId] = {
                    'lon': source['lon'] ,
                    'lat': source['lat'] ,
                    'level': sourceLevel ,
                    //'style': source['style'] ,
                    // no style attribute added to actual REPAiR data
                    'color': source.color,
                    'label': source.label
                };
                nodesDataFlow[targetId] = {
                    'lon': target['lon'],
                    'lat': target['lat'],
                    'level': targetLevel,
                    //'style': target['style'],
                    // no style attribute added to actual REPAiR data
                    'color': target.color,
                    'label': target.label
                };

                // drawTotalPath, if drawPath is chosen, every path is shown divided by materials which is not intended
                this.drawTotalPath(sxp, syp, txp, typ, flow.labelTotal, totalStroke, sourceLevel, targetLevel, bothways, connection,Bthis, flowsData, nodesData, strokeWidthPerFlow, totalStrokeWidths)
               // this.drawPath(sxp, syp, txp, typ, flow.style, flow.label, offset, strokeWidth, totalStroke, sourceLevel, targetLevel, bothways, connection)

            }


            // use addpoint for each node in nodesDataFlow
            Object.values(nodesDataFlow).forEach(function (node) {
                _this.addPoint(node.lon, node.lat,
                    node.level, node.label, node.color);
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
            return 6;
        }

        // make adjustments if using other datasets
        defineRadiusZoom(level){
            var zoomLevel = this.map.getZoom();
            var radius = this.defineRadius(level);

            if (zoomLevel < 10){
                return radius * (zoomLevel/15);
            }
            if (zoomLevel < 14){
                return radius * (zoomLevel/5);
            }
            else {
                return radius * zoomLevel/3;}
        }

        // make adjustments if using other datasets
        defineStrokeZoom(stroke){
            var zoomLevel = this.map.getZoom();

            var stroke = stroke;

            if (zoomLevel < 10) {
                return stroke * (zoomLevel/2)
            }
            if (zoomLevel < 14) {
                return stroke * (zoomLevel*2)
            }
            if (zoomLevel < 17) {
                return stroke * (zoomLevel*4)
            }
            else {
                return stroke * (zoomLevel*6);
            }
        }


        //function to add source nodes to the map
        addPoint(lon, lat, level, nodeLabel, color) {
            var x = this.projection([lon, lat])[0],
                y = this.projection([lon, lat])[1];

            var radius = this.defineRadiusZoom(level)/2;

            // tooltip
            var tooltip = d3.select("body")
                .append("div")
                .attr("class", "tooltip")
                .style("opacity", 0.9)
                .style("z-index", 500);

            var point = this.g.append("g")
                .attr("class", "node")
                .append("circle")
                .attr("cx", x)
                .attr("cy", y)
                .attr("r", radius)
                .style("fill", color)
                .style("fill-opacity", 1)
                .style("stroke", 'lightgrey')
                .style("stroke-width", 0.4)
                .on("mouseover", function (d) {
                    d3.select(this).style("cursor", "pointer"),
                        tooltip.transition()
                            .duration(200)
                            .style("opacity", 0.9);
                        tooltip.html(nodeLabel)
                            .style("left", (d3.event.pageX) + "px")
                            .style("top", (d3.event.pageY - 28) + "px")
                })
                .on("mouseout", function (d) {
                        tooltip.transition()
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
        totalOffset(sxpa, sypa, txpa, typa, dxp, dyp, flowLength, offset, totalStroke, bothways, connection){
            if (bothways.includes(connection) === true) {
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

        getPointsFromTotalPath(sxp, syp, txp, typ, totalStroke, sourceLevel, targetLevel, bothways, connection){
            var pathLengthValues = this.adjustedPathLength(sxp, syp, txp, typ, sourceLevel, targetLevel);
            var dxp = pathLengthValues[0],
                dyp = pathLengthValues[1],
                sxpa = pathLengthValues[2],
                sypa = pathLengthValues[3],
                txpa = pathLengthValues[4],
                typa = pathLengthValues[5],
                flowLength = pathLengthValues[6];

            var offset = totalStroke / 2;

            var totalOffset = this.totalOffset(sxpa, sypa, txpa, typa, dxp, dyp, flowLength, offset, totalStroke, bothways, connection);
            var sxpao = totalOffset[0],
                sypao = totalOffset[1],
                txpao = totalOffset[2],
                typao = totalOffset[3];

            return [sxpao,sypao,txpao,typao];
        }

        uuidv4() {
            return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
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
        drawTotalPath(sxp, syp, txp, typ, labelTotal, totalStroke, sourceLevel, targetLevel, bothways, connection,
                      Bthis, flowsData, nodesData, strokeWidthPerFlow, totalStrokeWidths) {

            var totalPoints = this.getPointsFromTotalPath(sxp, syp, txp, typ, totalStroke, sourceLevel, targetLevel, bothways, connection);
            var sxpao = totalPoints[0],
                sypao = totalPoints[1],
                txpao = totalPoints[2],
                typao = totalPoints[3];

            var adjustedPathLength = this.adjustedPathLength(sxp, syp, txp, typ, sourceLevel, targetLevel);
            var dxp = adjustedPathLength[0],
                dyp = adjustedPathLength[1],
                flowLength = adjustedPathLength[6];

            var triangleData = this.defineTriangleData(sxpao, sypao, txpao, typao, targetLevel, totalStroke, flowLength, dxp, dyp);

            //unique id for each clip path is necessary
            var uid = this.uuidv4();

            // tooltip
            var tooltip = d3.select("body")
                .append("div")
                .attr("class", "tooltip")
                .style("opacity", 0.9)
                .style("z-index", 500);

            this.drawArrowhead(sxpao, sypao, txpao, typao, targetLevel, totalStroke, flowLength, dxp, dyp, uid);

            var flowsTotal = this.g.append("line")
                .attr("x1", sxpao)
                .attr("y1", sypao)
                .attr("x2", txpao)
                .attr("y2", typao)
                .attr("id", "#line")
                .attr("clip-path", "url(#clip" + uid +")")
                .attr("stroke-width", totalStroke)
                .attr("stroke", "grey")
                .attr("stroke-opacity", 0.3)
                .on("click", function(){
                    for (var key in flowsData) {
                        var flow = flowsData[key];
                        var sourceId = flow.source,
                            targetId = flow.target;

                        if (sourceId + '-' + targetId === connection) {
                            var source = nodesData[sourceId],
                                target = nodesData[targetId];

                            var sourceCoords = [source['lon'], source['lat']],
                                targetCoords = [target['lon'], target['lat']];

                            //add projection to source and target coordinates
                            var sxp = Bthis.projection(sourceCoords)[0],
                                syp = Bthis.projection(sourceCoords)[1],
                                txp = Bthis.projection(targetCoords)[0],
                                typ = Bthis.projection(targetCoords)[1];

                            var strokeWidth = strokeWidthPerFlow[key][0],
                                offset = strokeWidthPerFlow[key][1],
                                totalStroke = totalStrokeWidths[connection];

                            var sourceLevel = source.level,
                                targetLevel = target.level;

                            Bthis.drawPath(sxp, syp, txp, typ, flow.color, flow.label, offset, strokeWidth, totalStroke, sourceLevel, targetLevel, bothways, connection)
                        }
                    }

                })
                .on("mouseover", function () {
                    d3.select(this).node().parentNode.appendChild(this);
                    d3.select(this).style("cursor", "pointer"),
                        tooltip.transition()
                            .duration(200)
                            .style("opacity", 0.8);
                        tooltip.html(labelTotal)
                            .style("left", (d3.event.pageX) + "px")
                            .style("top", (d3.event.pageY - 28) + "px")
                        flowsTotal.attr("stroke-opacity",0.4)
                            .attr("stroke", "black")
                })
                .on("mouseout", function () {
                        tooltip.transition()
                            .duration(500)
                            .style("opacity", 0)
                        flowsTotal.attr("stroke-opacity",0.3)
                            .attr("stroke", "grey")
                })
            ;
        }

        // function to draw path divided by materials
        drawPath(sxp, syp, txp, typ, color, label, offset, strokeWidth, totalStroke, sourceLevel, targetLevel, bothways, connection) {

            var pathLengthValues = this.adjustedPathLength(sxp, syp, txp, typ, sourceLevel, targetLevel);
            var dxp = pathLengthValues[0],
                dyp = pathLengthValues[1],
                sxpa = pathLengthValues[2],
                sypa = pathLengthValues[3],
                txpa = pathLengthValues[4],
                typa = pathLengthValues[5],
                flowLength = pathLengthValues[6];

            //unique id for each clip path is necessary
            var uid = this.uuidv4();

            // tooltip
            var tooltip = d3.select("body").append("div")
                .attr("class", "tooltip")
                .style("opacity", 0.9)
                .style("z-index", 500);

            var totalOffset = this.totalOffset(sxpa, sypa, txpa, typa, dxp, dyp, flowLength, offset, totalStroke, bothways, connection);
            var sxpao = totalOffset[0],
                sypao = totalOffset[1],
                txpao = totalOffset[2],
                typao = totalOffset[3];

            var totalPoints = this.getPointsFromTotalPath(sxp, syp, txp, typ, totalStroke, sourceLevel, targetLevel, bothways, connection);
            var sxpaot = totalPoints[0],
                sypaot = totalPoints[1],
                txpaot = totalPoints[2],
                typaot = totalPoints[3];

            var triangleDataf = this.defineTriangleData(sxpaot, sypaot, txpaot, typaot, targetLevel, totalStroke, flowLength, dxp, dyp);

            this.drawArrowhead(sxpaot, sypaot, txpaot, typaot, targetLevel, totalStroke, flowLength, dxp, dyp, uid);

            var flows = this.g.append("line")
                .attr("class", "fraction")
                .attr("x1", sxpao)
                .attr("y1", sypao)
                .attr("x2", txpao)
                .attr("y2", typao)
                .attr("stroke-width", strokeWidth)
                .attr("stroke", color)
                .attr("stroke-opacity", 0.8)
                .attr("clip-path", "url(#clip" + uid +")")
                .on("click", function(){
                        d3.selectAll("line.fraction").remove();
                        tooltip.remove()
                })
                .on("mouseover", function(){
                    d3.select(this).node().parentNode.appendChild(this);
                    d3.select(this).style("cursor", "pointer"),
                        tooltip.transition()
                            .duration(200)
                            .style("opacity", 0.9);
                        tooltip.html(label)
                            .style("left", (d3.event.pageX) + "px")
                            .style("top", (d3.event.pageY - 28) + "px")
                        flows.attr("stroke-opacity", 1)
                })
                .on("mouseout", function(d) {
                        tooltip.transition()
                            .duration(500)
                            .style("opacity", 0)
                        flows.attr("stroke-opacity", 0.8)
                    }
                );
        }

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
        }

    }

    return FlowMap;
});
