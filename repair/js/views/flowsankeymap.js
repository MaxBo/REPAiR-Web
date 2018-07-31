define(['views/baseview', 'visualizations/flowmap', 'leaflet',
        'leaflet/dist/leaflet.css', 'static/css/flowmap.css'],

function(BaseView, FlowMap, L){

    /**
    *
    * @author Christoph Franke, Vilma Jochim
    * @name module:views/FlowSankeyMapView
    * @augments module:views/BaseView
    */
    var FlowSankeyMapView = BaseView.extend( 
        /** @lends module:views/FlowSankeyView.prototype */
        {

        /**
        * view on a leaflet map with flows and nodes overlayed
        *
        * @param {Object} options
        * @param {HTMLElement} options.el      element the view will be rendered in
        *
        * @constructs
        * @see http://backbonejs.org/#View
        */
        initialize: function(options){
            FlowSankeyMapView.__super__.initialize.apply(this, [options]);
            this.render();
            
            this.locations = {};
            this.flows = {};
        },

        /*
        * dom events (managed by jquery)
        */
        events: {
        },

        /*
        * render the view
        */
        render: function(){
        
            var map = new L.Map(this.el, {
                    center: [52.41, 4.95], 
                    zoomSnap: 0.25, 
                    zoom: 10.5, 
                    minZoom: 5,
                    maxZoom: 18
                })
                .addLayer(new L.TileLayer("http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"));
            var flowMap = new FlowMap(map);
            function reset(){
                flowMap.reset();
                flowMap.render(transformed.nodes, transformed.flows, transformed.styles);
            }
            //map.on("zoomend", reset);
            //reset();
            var collection = this.actors;
            //flowMap.renderCsv("/static/data/countries.topo.json", "/static/data/nodes.csv", "/static/data/flows.csv");
        },
        
        /**
         *
         * @param {Object} flow
         * @param {Object} flow.source   source node with id, name and color
         * @param {Object} flow.target   target node with id, name and color
         * @param {String} flow.units
         * @param {Number} flow.value
         */
        addFlow: function(flow){
            this.flows[flowId] = flow;
        },

        /*
        * transform the models, their links and the stocks to a json-representation
        * readable by the sankey-diagram
        */
        transformData: function(actors, locations, locations2, materials, actor2actor, levels) {

            // defining object that will store the style information: node color & radius, flow color
            var styles = {};
    
            // Data for administrative levels
            var levelsData ={};
            levels.forEach(function(level) {
                var name = level.name;
                levelsData[level.level] = name;
            });
    
            // further actor data information that is later on inserted into acotors data with coordinates
            actorsName = {};
            actorsActivity = {};
            actorsActivityId = {};
            actors.forEach(function(actor) {
               var name = actor.name,
                   activity = actor.activitygroup_name,
                   activityId = actor.activitygroup;
                actorsName[actor.id] = name
                actorsActivity[actor.id] = activity
                actorsActivity[actor.id] = activityId
            });
    
    
            var uniqueActivity = new Set();
            var ActivityArray = [];
            // object with actors locations and further information
            var locationsData = {};
            i=0;
            locations.forEach(function (location) {
                var actorId = location.id,
                    coordinates = location.point_on_surface.coordinates;
                var lon = coordinates[0],
                    lat = coordinates[1];
                var level = location.level,
                    levelName = levelsData[location.level],
                    activityId = 2;
                var label = '<b>Name: </b>' + location.name +'<br><b>Administrative Level: </b>' + levelName;
                locationsData[location.id]= {
                    'name': location.name,
                    'lon': lon,
                    'lat': lat,
                    'level': level,
                    'style': activityId,
                    'label': label
                }
                ActivityArray.push(activityId)
                uniqueActivity = uniqueActivity.add(activityId)
                i += 1;
    
            });
    
            // locations from dataset of individual actors; dataset has a slightly different data structure
            locations2.features.forEach(function (location2) {
                var actorId = location2.properties.actor,
                    geometry = location2.geometry;
                var coordinates = location2.geometry.coordinates;
                var lon = coordinates[0],
                    lat = coordinates[1];
                var level = location2.properties.level,
                    levelName = 'Actor',
                    name = actorsName[location2.properties.actor],
                    activity = actorsActivity[location2.properties.actor],
                    activityId = 3;
                ActivityArray.push(activityId)
                var label = '<b>Name: </b>' + name +'<br><b>Administrative Level: </b>' + levelName + '<b><br>Activity: </b>' + activity;
                locationsData[actorId]= {
                    'name': name,
                    'lon': lon,
                    'lat': lat,
                    'level': level,
                    'style': activityId,
                    'label': label
                }
                uniqueActivity = uniqueActivity.add(activityId)
                i += 1;
    
            });
    
            // define boundingbox
            var topLeft = [10000, 0],
                bottomRight = [0, 10000];
            Object.values(locationsData).forEach(function (location){
                var lon = location.lon,
                    lat = location.lat;
                topLeft = [Math.min(topLeft[0], lon), Math.max(topLeft[1], lat)];
                bottomRight = [Math.max(bottomRight[0], lon), Math.min(bottomRight[1], lat)];
            });
    
    
            // define color for the nodes by activity and store it in styles
            var nodeColor = d3.scale.linear()
                .range (["#0077BB", "#33BBEE","#009988","#EE7733","#CC3311","#EE3377"])
                .domain([0, 1/5*(uniqueActivity.size-1), 2/5*(uniqueActivity.size-1), 3/5*(uniqueActivity.size-1), 4/5*(uniqueActivity.size-1), (uniqueActivity.size-1)])
                .interpolate(d3.interpolateHsl);
            var i = 0;
    
            uniqueActivity.forEach(function (activity) {
                var color = nodeColor(i);
                styles[activity] = {'nodeColor': color};
                i += 1;});
    
    
            // define fixed node radius depending on spatial level
            function defineRadius(level){
                var level = level;
                if (level === 10) {return 11}
                if (level === 8) {return 16}
                if (level === 6) {return 21}
                if (level === 4) {return 26}
                else {return 6}
            };
    
            for (var key in locationsData){
                var level = locationsData[key].level;
                var radius = defineRadius(level);
                styles[level] = {'radius': radius};
            };
    
    
            // materials data
            var materialsData = {};
            materials.forEach(function (material) {
                materialsData[material.id] = {'name': material.name, 'level': material.level}
            });
    
    
            // data for flows
            var uniqueMaterials = new Set();
            var flowsData = {};
            i = 0;
            actor2actor.forEach(function (flow) {
                flow.composition.fractions.forEach(function (fraction) {
                    var amount = flow.amount * fraction.fraction,
                        totalAmount = flow.amount,
                        material = materialsData[fraction.material],
                        complabel = (flow.waste) ? '<b>Waste</b>b>' : '<b>Product</b>',
                        origin = locationsData[flow.origin],
                        originName = (origin) ? origin.name : '',
                        destination = locationsData[flow.destination],
                        destinationName = (destination) ? destination.name : '',
                        flowlabel = originName + '&#10132; '  + destinationName,
                        label = flowlabel + '<br>' +complabel + ': ' + flow.composition.name + '<b><br>Material: </b>' + material.name + '<b><br>Amount: </b>' + amount + ' t/year',
                        labelTotal = flowlabel + '<br>' + complabel + ': ' + flow.composition.name + '<b><br>Amount: </b>' + totalAmount + ' t/year';
                    flowsData[i] = {
                        'id': flow.id,
                        'source': flow.origin,
                        'target': flow.destination,
                        'value': amount,
                        'valueTotal':totalAmount,
                        'label': label,
                        'labelTotal': labelTotal,
                        'style': fraction.material
                    };
                    uniqueMaterials.add(fraction.material);
                    i += 1;
                });
            });
    
            //define colors for individual materials and store in styles
            var materialColor = d3.scale.linear()
                .range (["#4477AA", "#66CCEE","#228833","#CCBB44","#EE6677","#AA3377"])
                .domain([0, 1/5*(uniqueMaterials.size-1), 2/5*(uniqueMaterials.size-1), 3/5*(uniqueMaterials.size-1), 4/5*(uniqueMaterials.size-1), (uniqueMaterials.size-1)])
                .interpolate(d3.interpolateHsl);
    
            var i = 0;
    
            uniqueMaterials.forEach(function (materialId) {
                var color = materialColor(i);
                styles[materialId] = {'color':color};
                i += 1;
            });
    
    
            return {flows: flowsData, nodes: locationsData, styles: styles, bbox: [topLeft, bottomRight]};
        }

    });
    return FlowSankeyMapView;
}
);