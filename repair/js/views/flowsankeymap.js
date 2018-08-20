define(['underscore', 'views/baseview', 'collections/gdsecollection',
        'collections/geolocations',
        'visualizations/flowmap', 'leaflet', 'leaflet-fullscreen',
        'leaflet/dist/leaflet.css', 'static/css/flowmap.css',
        'leaflet-fullscreen/dist/leaflet.fullscreen.css'],

function(_, BaseView, GDSECollection, GeoLocations, FlowMap, L){

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
            _.bindAll(this, 'update');
            this.render();
            this.caseStudyId = options.caseStudyId;
            this.keyflowId = options.keyflowId;
            this.materials = options.materials;

            this.locations = {};
            this.flows = {};
            this.nodes = {};
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
            this.leafletMap = new L.Map(this.el, {
                    center: [52.41, 4.95],
                    zoomSnap: 0.25,
                    zoom: 10.5,
                    minZoom: 5,
                    maxZoom: 25
                })
                .addLayer(new L.TileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"));
            this.flowMap = new FlowMap(this.leafletMap);
            this.leafletMap.addControl(new L.Control.Fullscreen({position:'topright'}));
            this.leafletMap.on("zoomend", this.update);

            var displayMaterial = L.control({position: 'bottomleft'});
            var div = document.createElement('div'),
                checkbox = document.createElement('input'),
                label = document.createElement('label'),
                _this = this;
            checkbox.type = "checkbox";
            checkbox.style.pointerEvents = "none";
            checkbox.classList.add('form-control');
            div.style.background = "rgba(255, 255, 255, 0.5)";
            div.style.padding = "10px";
            div.style.cursor = "pointer";
            label.innerHTML = gettext('Display materials');
            div.appendChild(checkbox);
            div.appendChild(label);
            displayMaterial.onAdd = function (map) {
                return div;
            };
            displayMaterial.addTo(this.leafletMap);

            div.addEventListener ("click", function(){
                checkbox.checked = !checkbox.checked;
                _this.data = _this.transformData();
                _this.update();
            });
        },

        update: function(){
            if (!this.data) return;
            this.flowMap.reset(this.data.bbox);
            this.flowMap.render(this.data.nodes, this.data.flows);
        },

        zoomToFit: function(){
            if (!this.data) return;
            var bbox = this.data.bbox;
            // leaflet uses lat/lon in different order
            this.leafletMap.fitBounds([
                [this.data.bbox[0][1], this.data.bbox[0][0]],
                [this.data.bbox[1][1], this.data.bbox[1][0]]
            ]);
        },

        rerender: function(zoomToFit){
            var _this = this;
            this.loader.activate();
            this.prefetchLocations(function(){
                _this.data = _this.transformData();
                _this.loader.deactivate();
                _this.update();
                if (zoomToFit) _this.zoomToFit();
            })
        },

        addFlows: function(flows){
            var _this = this;
                flows = (flows instanceof Array) ? flows: [flows];
            flows.forEach(function(flow){
                _this.flows[flow.id] = flow;
            })
        },

        addNodes: function(nodes){
            var _this = this,
                nodes = (nodes instanceof Array) ? nodes: [nodes];
            nodes.forEach(function(node){
                _this.nodes[node.id] = node;
            })
        },

        getNodes: function(){
            return Object.values(this.nodes);
        },

        getFlows: function(){
            return Object.values(this.flows);
        },

        removeFlows: function(flows){
            var _this = this;
                flows = (flows instanceof Array) ? flows: [flows];
            flows.forEach(function(flow){
                delete _this.flows[flow.id];
            })
        },

        removeNodes: function(nodes, unusedOnly){
            var _this = this,
                nodes = (nodes instanceof Array) ? nodes: [nodes],
                usedNodes = new Set();
            if (unusedOnly) {
                Object.values(this.flows).forEach(function(flow){
                    usedNodes.add(flow.get('origin'));
                    usedNodes.add(flow.get('destination'));
                })
            }
            nodes.forEach(function(node){
                if (!usedNodes.has(node.id))
                    delete _this.nodes[node.id];
            })
        },

        clear: function(){
            this.nodes = {};
            this.flows = {};
            this.rerender();
        },

        prefetchLocations: function(callback){
            var promises = [],
                _this = this;
            for (var nodeId in this.nodes) {
                if (nodeId in _this.locations) continue;
                var adminLocations = new GeoLocations([], {
                    apiTag: 'adminLocations',
                    apiIds: [this.caseStudyId, this.keyflowId]
                });
                promises.push(adminLocations.fetch({
                    data: { actor: nodeId },
                    success: function(coll){
                        var adminLoc = coll.first();
                        // only add nodes with locations
                        if (adminLoc) {
                            id = adminLoc.get('properties').actor;
                            _this.locations[id] = adminLoc;
                        }
                    }
                }));
            }
            Promise.all(promises).then(callback);
        },
        //ToDo: actors, activities, groups may have same id, introduce prefix (to store in locations, nodesData..)

        /*
        * transform the models, their links and the stocks to a json-representation
        * readable by the sankey-diagram
        */
        transformData: function(splitByComposition) {

            // defining object that will store the style information: node color & radius, flow color
            var nodes = [],
                links = [],
                // boundingbox
                topLeft = [10000, 0],
                bottomRight = [0, 10000];
                _this = this;

            for (var nodeId in this.nodes) {
                var location = _this.locations[nodeId];
                if (!location) continue;
                var node = this.nodes[nodeId],
                    id = node.id,
                    location = _this.locations[node.id],
                    geom = location.get('geometry');
                if (!geom) continue;

                var coords = geom.get('coordinates'),
                    lon = coords[0],
                    lat = coords[1];

                nodes.push({
                    id: node.id,
                    name: node.get('name'),
                    label: node.get('name'),
                    color: node.color,
                    lon: lon,
                    lat: lat,
                    level: -1
                })
                topLeft = [Math.min(topLeft[0], lon), Math.max(topLeft[1], lat)];
                bottomRight = [Math.max(bottomRight[0], lon), Math.min(bottomRight[1], lat)];
            };

            var uniqueMaterials = new Set();
            var i = 0;
            for (var flowId in this.flows) {
                var flow = this.flows[flowId],
                    composition = flow.get('composition'),
                    origin = _this.nodes[flow.get('origin')],
                    destination = _this.nodes[flow.get('destination')];
                if(!origin || !destination) continue;

                var wasteLabel = (flow.get('waste')) ? '<b>Waste</b>b>' : '<b>Product</b>',
                    flowlabel = origin.get('name') + '&#10132; '  + destination.get('name') + '<br>' + wasteLabel,
                    totalAmount = flow.get('amount'),
                    labelTotal = flowlabel + ': ' + composition.name + '<b><br>Amount: </b>' + totalAmount + ' t/year';

                if(splitByComposition){
                    composition.fractions.forEach(function(fraction){
                        var material = _this.materials.get(fraction.material),
                            amount = totalAmount * fraction.fraction,
                            label = flowlabel + ': ' + composition.name + '<b><br>Material: </b>' + material.get('name') + '<b><br>Amount: </b>' + amount + ' t/year';
                        links.push({
                            id: flow.id,
                            label: label,
                            source: flow.get('origin'),
                            target: flow.get('destination'),
                            value: amount,
                            material: material.id
                        })
                        uniqueMaterials.add(material.id);
                        i++;
                    })
                    //define colors for individual materials and store in styles
                    var materialColor = d3.scale.linear()
                        .range (["#4477AA", "#66CCEE","#228833","#CCBB44","#EE6677","#AA3377"])
                        .domain([0, 1/5*(uniqueMaterials.size-1), 2/5*(uniqueMaterials.size-1), 3/5*(uniqueMaterials.size-1), 4/5*(uniqueMaterials.size-1), (uniqueMaterials.size-1)])
                        .interpolate(d3.interpolateHsl);

                    var matColors = {};
                    i = 0;
                    uniqueMaterials.forEach(function (materialId) {
                        var color = materialColor(i);
                        matColors[materialId] = color;
                        i += 1;
                    });

                    links.forEach(function(link){
                        link.color = matColors[link.material];
                    })
                }
                else {
                    links.push({
                        id: flow.id,
                        label: labelTotal,
                        source: flow.get('origin'),
                        target: flow.get('destination'),
                        color: origin.color,
                        value: totalAmount
                    })
                    i++;
                }
            }

            return {
                flows: links,
                nodes: nodes,
                bbox: [topLeft, bottomRight]
            }
        }

    });
    return FlowSankeyMapView;
}
);
