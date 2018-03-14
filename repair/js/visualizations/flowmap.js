define([
  'd3', 'topojson', 'd3-queue'
], function(d3, topojson, d3queue){

class FlowMap {

    constructor(container, options){
        var options = options || {};
        this.container = document.getElementById(container);
        
        // ToDo: include this projection somehow (d3 geoMercator is used)
        //this.projection = options.projection || 'EPSG:3857';
        
        this.width = options.width || this.container.getBoundingClientRect().width;
        this.height = options.height || this.width / 1.5;
        
        this.projection = d3.geo.mercator()
                            .center([25, 43])
                            .translate([this.width / 2, this.height / 2])
                            .scale(950);
        
        this.path = d3.geo.path().projection(this.projection);
        this.svg = d3.select(this.container)
                     .append("svg")
                     .attr("width", this.width)
                     .attr("height", this.height)
                     .append("g");
        this.g = this.svg.append("g");
        
    }
    
    render(nodes, flows){
        
        // remember scope of 'this' as context for functions with different scope
        var _this = this;
        
        //nodes data
        var nodesData = {};
        nodes.forEach(function(node) {
            nodesData[node.city] = {'city':node.city,'lon':node.lon,'lat':node.lat};
        });
        
        //flows data
        var flowsData = {};
        //get all flow-values from flowsData to use for path stroke-width
        var flowsValues = [];
        flows.forEach(function(flow) {
            flowsData[flow.id] = {'id':flow.id,'source':flow.source,'target':flow.target,'value':flow.value,'type':flow.type};
        flowsValues.push(parseInt(flow.value));
        });
    
        /*
        Daten definieren: 
        source_x, source_y, source_coord,
        target_x,target_y,target_coord 
        */
        for(key in flowsData) {
            // console.log(key)
        //source
            var source = flowsData[key].source, //die source wird aus den flowsData je key gezogen
                sourceX = nodesData[source]['lon'], //die source aus flowsData ist der key in nodesData und daraus werden koordinaten gezogen
                sourceY = nodesData[source]['lat'],
                sourceCoords = [sourceX, sourceY],
                //target
                target = flowsData[key].target,
                targetX = nodesData[target]['lon'],
                targetY = nodesData[target]['lat'],
                targetCoords = [targetX, targetY],
                //flow für Krümmung
                flow = [source, target],
        // console.log(flow)
            /* Pseudocode, um die Anzahl gleicher flows zu kriegen
                for each source, target same
                - count + 1, wenn source & target in flowsData gleich sind 
                - if (count = 7) {return bend 0:0.7;}
                    else if (count = 6) {return bend 0:0.6;}
                array.length()
                if (array.length = 7) {return bend 0:0.7;}
                */
        
        //color	
                color = flowsData[key].type,
        
        //define strokeWidth
                maxValue = Math.max.apply(null, flowsValues),
                maxWidth = 12,
                width= flowsData[key].value;
        
            this.strokeWidth = width / maxValue * maxWidth;
        
        // drawPath
            this.drawPath(sourceX, sourceY, targetX, targetY, 0.8, color)
        
        
        } //End for key in flowsData


        //**********************************************************************************************************************
        // adjust point size
        // get values per source
        // get the value for each individual source (that you find in node.city)
        var valuePerSource = {},
            pointValue = [];
    
        nodes.forEach(function(node){  //run through nodes
            // get value per source element
            var value = 0;
            flows.forEach(function(flow){  //  for each flow, if source == node.city add the flow.value to the defined value
                if (flow.source == node.city){
                    //console.log(flow.value)
                    value = value + parseInt(flow.value);
                }
            });
            valuePerSource[node.city] = value;
            pointValue.push(valuePerSource[node.city]);     //pointValue to get the values for calculating the max value
    
        });
    
        // get point size
        var maxPointValue = Math.max.apply(null,pointValue),
            maxPointSize = 12;

        // run through valuePerSource
        for (var key in valuePerSource){
            var pointSize = 4 + (valuePerSource[key] / maxPointValue * maxPointSize);             // (4+ so that the size is at least 4)calculate for each key the pointSize (value/maxValue * maxPointSize)
            valuePerSource[key] = pointSize                                          // like push: put the pointSize-Values into the object valuePerSource for each key
            console.log(pointSize)
        };


        // addpoint for each node
        nodes.forEach(function(node) {
            pointSize=valuePerSource[node.city]                 //under the valuePerSource object are pointSite - values per city which are calculated above; here we take the values
            if (pointSize == 0){pointSize=4}
            _this.addPoint(node.lon, node.lat,pointSize);
        });
    //**********************************************************************************************************************


    } 

    
    renderCsv(topoJson, nodesCsv, flowsCsv){
        var _this = this;
        
        function drawTopo(topojson) {
            var country = _this.g.selectAll(".country").data(topojson);
            _this.g.selectAll(".country")
                   .data(topojson)
                   .enter()
                   .append("path")
                   .attr("class", "country")
                   .attr("d", _this.path)
                   .attr("id", function(d,i) { return d.id; })
                   .style("fill", "lightgrey");
        }
        
        // Alle Daten werden über die queue Funktion parallel reingeladen, hier auf die Reihenfolge achten
        function loaded(error, world, nodes, flows) {
            //world data
            var countries = topojson.feature(world, world.objects.countries).features;
            drawTopo(countries);
            _this.render(nodes, flows);
        }
        d3queue.queue().defer(d3.json, topoJson)
                       .defer(d3.csv, nodesCsv)
                       .defer(d3.csv, flowsCsv)
                       .await(loaded);
    
    }


    //function to add points to the map
    addPoint(lon, lat, pointSize) {
        var x = this.projection([lon, lat])[0];
        var y = this.projection([lon, lat])[1];
    
        var point = this.g.append("g")
                          .attr("class", "gpoint")
                          .append("circle")
                          .attr("cx", x)
                          .attr("cy", y)
                          .attr("r", pointSize);
        // Größe der Punkte abhängig nach in & outflows
    //& farbe abhängig, ob mehr in- oder outflows
    }

    //function makeArc, that is used for drawPath
    makeArc(sx, sy, tx, ty, bend) {
        //sx,sy,tx,ty mit projection versehen
        var sxp = this.projection([sx,sy])[0],
            syp = this.projection([sx,sy])[1],
            txp = this.projection([tx,ty])[0],
            typ = this.projection([tx,ty])[1];

        var dx = txp - sxp,
            dy = typ - syp,
            dr = Math.sqrt(dx * dx + dy * dy) * bend;

        return "M" + sxp + "," + syp + "A" + dr + "," + dr +" 0 0,1 " + txp + "," + typ;
    }

    specifyColor(color) {
        if (color === 'organic') {return '#2e7b50';}
        if (color === 'plastic') {return '#4682b4';}
        if (color === 'construction') {return '#cc8400';}
        if (color === 'food') {return '#ebda09';}
        if (color === 'msw') {return '#348984';}
        if (color === 'hazardous') {return '#893464';}
        return 'white';
    }

    drawPath(sx,sy,tx,ty,bend,color) {
        // draw arrow
        // source: https://stackoverflow.com/questions/36579339/how-to-draw-line-with-arrow-using-d3-js
        var arrow = this.svg.append("marker")
                            .attr("id", "arrow")
                            .attr("refX", 6)
                            .attr("refY", 6)
                            .attr("markerWidth", 10)
                            .attr("markerHeight", 10)
                            .attr("orient", "auto")
                            .append("path")
                            .attr("d", "M 3 5.5 3.5 5.5" +      //left
                                " 4 6 " +                       //up
                                " 3.5 6.5  3 6.5 " +            //right
                                "3.5 6")                        //down
                            .style("fill", "black");
    
    
        var route = this.g.insert("path")
                        .attr("class", "route")
                        .attr("id","route")
                        .attr("d", this.makeArc(sx,sy,tx,ty,bend))
                        .style("stroke", this.specifyColor (color))
                        .style("stroke-width", this.strokeWidth)
                        //.style("stroke-dasharray", "9, 2")
                        .attr("marker-end", "url(#arrow)");
    }
}

return FlowMap;
});

/*

Aktuelle AUFGABEN

    *** - Farbe nach type
    *** - StrokeWidth: Breite nach value
        Vorgehen: value / maxValue * maxStrokeWidth
- Punkte
    - Größe der Punkte abhängig nach in & outflows
    - Farbe abhängig, ob mehr in- oder outflows

- Richtung anzeigen: 1 arrow mit marker-start oder marker-end, aber: bei bend funktioniert es nicht (bend einfügen) und anzeige in bestimmtem abstand
    - arcTween: mit animation?
    -transition https://github.com/d3/d3-transition#transition_attrTween
    - chained transition (dashedarray?)https://bl.ocks.org/mbostock/70d5541b547cc222aa02

- bend anpassen nach Anzahl von flows: bzw bend nach typ, da an gleicher stelle sein soll?

- Beziers statt arcs??
    - Bedingung einfügen: wenn type gleiches target xy und source xy hat, dann hintereinander verlaufen
*/
