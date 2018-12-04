define(['underscore', 'views/common/baseview', 'collections/gdsecollection',
        'collections/geolocations', 'collections/flows',
        'visualizations/flowmap', 'openlayers', 'utils/utils','leaflet',
        'leaflet-easyprint', 'leaflet-fullscreen',
        'leaflet.markercluster', 'leaflet.markercluster/dist/MarkerCluster.css',
        'leaflet.markercluster/dist/MarkerCluster.Default.css',
        'leaflet/dist/leaflet.css', 'static/css/flowmap.css',
        'leaflet-fullscreen/dist/leaflet.fullscreen.css'],

function(_, BaseView, GDSECollection, GeoLocations, Flows, FlowMap, ol, utils, L){

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
        * @param {HTMLElement} options.el      element the map will be rendered in
        * @param {string} options.template     id of the script element containing the underscore template to render this view
        * @param {Number} options.caseStudyId  id of the casestudy
        * @param {Number} options.keyflowId    id of the keyflow
        * @param {Number} options.materials    materials, should contain all materials used inside the keyflow
        *
        * @constructs
        * @see http://backbonejs.org/#View
        */
        initialize: function(options){
            FlowSankeyMapView.__super__.initialize.apply(this, [options]);
            _.bindAll(this, 'zoomed');
            this.caseStudy = options.caseStudy;
            this.caseStudyId = options.caseStudy.id;
            this.keyflowId = options.keyflowId;
            this.materials = options.materials;

            this.locations = {};
            this.flows = new Flows();
            this.actors = new GDSECollection();
            this.hideMaterials = {};
            this.displayWarnings = options.displayWarnings || false;
            this.render();
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
            //this.backgroundLayer = new L.TileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png");
            this.backgroundLayer = new L.TileLayer('https://cartodb-basemaps-{s}.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png',{
                attribution: '© OpenStreetMap contributors, © CartoDB'
            });
            var focusarea = this.caseStudy.get('properties').focusarea,
                poly = new ol.geom.MultiPolygon(focusarea.coordinates),
                interior = poly.getInteriorPoints(),
                centroid = interior.getCoordinates()[0];

            this.leafletMap = new L.Map(this.el, {
                    center: [centroid[1], centroid[0]],
                    zoomSnap: 0.25,
                    zoom: 10.5,
                    minZoom: 5,
                    maxZoom: 25
                })
                .addLayer(this.backgroundLayer);
            this.flowMap = new FlowMap(this.leafletMap);
            this.leafletMap.addControl(new L.Control.Fullscreen({position:'topright'}));
            this.leafletMap.addControl(new L.easyPrint({
                position: 'topright',
                filename: 'sankey-map',
                exportOnly: true,
                hideControlContainer: true
            }));
            this.leafletMap.on("zoomend", this.zoomed);

            var exportControls = L.control({position: 'topright'}),
                exportDiv = document.createElement('div'),
                exportImgBtn = document.createElement('button');
            exportImgBtn.classList.add('fas', 'fa-camera', 'btn', 'btn-primary', 'inverted');
            exportImgBtn.style.height = "30px";
            exportImgBtn.style.width = "30px";
            exportImgBtn.style.padding = "0px";
            exportDiv.appendChild(exportImgBtn);
            exportControls.onAdd = function (map) {
                return exportDiv;
            };
            exportControls.addTo(this.leafletMap);
            // easyprint is not customizable enough (buttons, remove menu etc.) and not touch friendly
            // workaround: hide it and pass on clicks (actually strange, but easyprint was still easiest to use export plugin out there)
            var easyprintCtrl = this.el.querySelector('.leaflet-control-easyPrint'),
                easyprintCsBtn = this.el.querySelector('.easyPrintHolder .CurrentSize');
            easyprintCtrl.style.visibility = 'hidden';
            exportImgBtn.addEventListener('click', function(){
                easyprintCsBtn.click();
            })

            var customControls = L.control({position: 'bottomleft'});
            this.materialCheck = document.createElement('input');
            this.animationCheck = document.createElement('input');
            this.clusterCheck = document.createElement('input');
            this.actorCheck = document.createElement('input');

            var div = document.createElement('div'),
                matLabel = document.createElement('label'),
                aniLabel = document.createElement('label'),
                actorLabel = document.createElement('label'),
                clusterLabel = document.createElement('label'),
                _this = this;

            matLabel.innerHTML = gettext('Display materials');
            aniLabel.innerHTML = gettext('Animate flows');
            clusterLabel.innerHTML = gettext('Cluster locations');
            actorLabel.innerHTML = gettext('Show actors');

            [this.materialCheck, this.clusterCheck,
            this.animationCheck, this.actorCheck].forEach(function(checkbox){
                checkbox.type = "checkbox";
                checkbox.style.transform = "scale(2)";
                checkbox.style.pointerEvents = "none";
                checkbox.style.marginRight = "10px";
            })

            this.actorCheck.checked = true;
            div.style.background = "rgba(255, 255, 255, 0.5)";
            div.style.padding = "10px";
            div.style.cursor = "pointer";

            var matDiv = document.createElement('div'),
                actorDiv = document.createElement('div'),
                aniDiv = document.createElement('div'),
                aniCheckWrap = document.createElement('div'),
                aniToggleDiv = document.createElement('div'),
                toggleAniBtn = document.createElement('button'),
                clusterDiv = document.createElement('div');

            toggleAniBtn.classList.add('glyphicon', 'glyphicon-chevron-right');
            matDiv.appendChild(this.materialCheck);
            matDiv.appendChild(matLabel);
            matDiv.style.cursor = 'pointer';
            actorDiv.appendChild(this.actorCheck);
            actorDiv.appendChild(actorLabel);
            actorDiv.style.cursor = 'pointer';
            clusterDiv.appendChild(this.clusterCheck);
            clusterDiv.appendChild(clusterLabel);
            clusterDiv.style.cursor = 'pointer';
            aniCheckWrap.appendChild(this.animationCheck);
            aniCheckWrap.appendChild(aniLabel);
            aniDiv.appendChild(aniCheckWrap);
            aniDiv.appendChild(toggleAniBtn);
            aniCheckWrap.style.cursor = 'pointer';
            aniToggleDiv.style.visibility = 'hidden';

            var aniLinesLabel = document.createElement('label'),
                aniDotsLabel = document.createElement('label');

            this.aniLinesRadio = document.createElement('input');
            this.aniLinesRadio.checked = true;
            this.aniDotsRadio = document.createElement('input');
            this.aniLinesRadio.type = 'radio';
            this.aniDotsRadio.type = 'radio';
            this.aniLinesRadio.name = 'animation';
            this.aniDotsRadio.name = 'animation';

            aniCheckWrap.style.float = 'left';
            aniCheckWrap.style.marginRight = '5px';
            aniToggleDiv.style.float = 'left';
            toggleAniBtn.style.float = 'left';
            aniLinesLabel.style.marginRight = '3px';

            aniLinesLabel.innerHTML = 'lines only';
            aniDotsLabel.innerHTML = 'dotted';
            aniLinesLabel.appendChild(this.aniLinesRadio);
            aniDotsLabel.appendChild(this.aniDotsRadio);
            aniToggleDiv.appendChild(aniLinesLabel);
            aniToggleDiv.appendChild(aniDotsLabel);

            customControls.onAdd = function (map) {
                return div;
            };
            customControls.addTo(this.leafletMap);

            matDiv.addEventListener("click", function(){
                _this.materialCheck.checked = !_this.materialCheck.checked;
                _this.rerender();
            });
            clusterDiv.addEventListener("click", function(){
                _this.clusterCheck.checked = !_this.clusterCheck.checked;
                _this.rerender();
            });
            aniCheckWrap.addEventListener("click", function(){
                _this.animationCheck.checked = !_this.animationCheck.checked;
                _this.flowMap.toggleAnimation(_this.animationCheck.checked);
            });
            toggleAniBtn.addEventListener("click", function(){
                aniToggleDiv.style.visibility = (aniToggleDiv.style.visibility == 'hidden') ? 'visible': 'hidden';
            });
            aniToggleDiv.addEventListener("click", function(){
                _this.rerender();
            });
            actorDiv.addEventListener("click", function(){
                _this.actorCheck.checked = !_this.actorCheck.checked;
                _this.rerender();
            });

            div.appendChild(actorDiv);
            div.appendChild(document.createElement('br'));
            div.appendChild(matDiv);
            div.appendChild(document.createElement('br'));
            div.appendChild(clusterDiv);
            div.appendChild(document.createElement('br'));
            div.appendChild(aniDiv);
            div.appendChild(document.createElement('br'));
            div.appendChild(aniToggleDiv);
            div.appendChild(document.createElement('br'));

            var legendControl = L.control({position: 'bottomright'});
            this.legend = document.createElement('div');
            this.legend.style.background = "rgba(255, 255, 255, 0.5)";
            this.legend.style.visibility = 'hidden';
            legendControl.onAdd = function () { return _this.legend; };
            legendControl.addTo(this.leafletMap);
        },

        toggleMaterials(){
            var show = this.materialCheck.checked,
                visibility = (show) ? 'visible': 'hidden';
            this.legend.style.visibility = visibility;
        },

        updateLegend(data){
            var data = data || this.data,
                _this = this;
            this.legend.innerHTML = '';
            var matColors = data.materialColors;
            // ToDo: inefficient, done too often for just toggling visibility
            Object.keys(matColors).forEach(function(matId){
                var material = _this.materials.get(matId),
                    color = matColors[matId],
                    div = document.createElement('div'),
                    text = document.createElement('div'),
                    check = document.createElement('input'),
                    colorDiv = document.createElement('div');
                div.style.height = '25px';
                div.style.cursor = 'pointer';
                text.innerHTML = material.get('name');
                text.style.fontSize = '1.3em';
                text.style.overflow = 'hidden';
                text.style.whiteSpace = 'nowrap';
                text.style.textOverflow = 'ellipsis';
                colorDiv.style.width = '20px';
                colorDiv.style.height = '100%';
                colorDiv.style.textAlign = 'center';
                colorDiv.style.background = color;
                colorDiv.style.float = 'left';
                check.type = 'checkbox';
                check.checked = !_this.hideMaterials[matId];
                check.style.pointerEvents = 'none';
                div.appendChild(colorDiv);
                div.appendChild(text);
                colorDiv.appendChild(check);
                _this.legend.appendChild(div);
                div.addEventListener('click', function(){
                    check.checked = !check.checked;
                    _this.hideMaterials[matId] = !check.checked;
                    _this.flowMap.toggleTag(matId, check.checked);
                })
                _this.flowMap.toggleTag(matId, check.checked)
            });
        },

        zoomed: function(){
            // zoomend always is triggered before clustering is done -> reset clusters
            this.clusterGroupsDone = 0;
        },

        toggleClusters(){
            var _this = this,
                show = this.clusterCheck.checked;
            // remove cluster layers from map
            this.leafletMap.eachLayer(function (layer) {
                if (layer !== _this.backgroundLayer)
                    _this.leafletMap.removeLayer(layer);
            });
            this.clusterGroups = {};
            // no clustering without data or clustering unchecked
            if (!this.data || !show) return;
            this.flowMap.clear();
            var nodes = Object.values(_this.data.nodes),
                rmax = 30;
            var nClusterGroups = 0;
                clusterPolygons = [];

            function drawClusters(){
                var data = _this.transformMarkerClusterData();
                // remove old cluster layers
                clusterPolygons.forEach(function(layer){
                    _this.leafletMap.removeLayer(layer);
                })
                clusterPolygons = [];
                _this.resetMapData(data, false);
                //if (!_this.hullCheck.checked) return;
                //Object.values(_this.clusterGroups).forEach(function(clusterGroup){
                    //clusterGroup.instance._featureGroup.eachLayer(function(layer) {
                        //if (layer instanceof L.MarkerCluster) {
                            //var clusterPoly = L.polygon(layer.getConvexHull());
                            //clusterPolygons.push(clusterPoly);
                            //_this.leafletMap.addLayer(clusterPoly);
                        //}
                    //})
                //})
            }

            // add cluster layers
            nodes.forEach(function(node){
                if (!node.group) return;
                var clusterId = node.group.id,
                    group = _this.clusterGroups[clusterId];
                // create group if not existing
                if (!group && node.group != null){
                    var clusterGroup = new L.MarkerClusterGroup({
                        maxClusterRadius: 2 * rmax,
                        iconCreateFunction: function(cluster) {
                            return L.divIcon({ iconSize: 0 });
                        },
                        animate: false
                    });
                    group = {
                        color: node.group.color,
                        label: node.group.name,
                        instance: clusterGroup
                    };
                    _this.clusterGroups[clusterId] = group;
                    _this.leafletMap.addLayer(clusterGroup);
                    clusterGroup.on('animationend', function(){
                        _this.clusterGroupsDone++;
                        // all cluster animations are done -> transform data
                        // according to current clustering
                        if (_this.clusterGroupsDone === nClusterGroups){
                            drawClusters();
                        }
                    })
                    nClusterGroups++;
                }
                var marker = L.marker([node['lat'], node['lon']], {
                    icon: L.divIcon({ iconSize: 0 }),
                    opacity: 0
                });
                marker.id = node.id;
                group.instance.addLayer(marker);
            });
            drawClusters();
        },

        resetMapData: function(data, zoomToFit) {
            this.data = data;
            this.flowMap.clear();
            this.flowMap.addNodes(data.nodes);
            this.flowMap.addFlows(data.flows);
            this.flowMap.showNodes = (this.actorCheck.checked) ? true: false;
            this.flowMap.dottedLines = (this.aniDotsRadio.checked) ? true: false;
            this.flowMap.resetView();
            this.updateLegend();
            if (zoomToFit) this.flowMap.zoomToFit();
        },

        rerender: function(zoomToFit){
            var _this = this;
            if(this.actors.length === 0) {
                this.clear();
                return;
            }
            this.loader.activate();
            this.prefetchLocations(function(){
                var splitByComposition = _this.materialCheck.checked;
                var data = _this.transformData(
                    _this.actors, _this.flows, _this.locations,
                    {
                        splitByComposition: splitByComposition
                    }
                );
                _this.loader.deactivate();
                if (_this.displayWarnings && data.warnings.length > 0) {
                    var msg = '';
                    data.warnings.forEach(function(warning){
                        msg += warning + '<br>';
                    })
                    _this.alert(msg);
                }
                _this.resetMapData(data, zoomToFit);
                _this.toggleClusters();
                _this.toggleMaterials();
            })
        },

        /*
        additional to the usual attributes the flow should have the attribute
        'color'
        */
        addFlows: function(flows){
            var _this = this;
                flows = (flows instanceof Array) ? flows: [flows];
            flows.forEach(function(flow){
                _this.flows.add(flow);
            })
        },

        /*
        additional to the usual attributes the nodes should have the attributes
        'color' and 'group' (object with attr. 'color', 'name' and 'id')
        */
        addNodes: function(nodes){
            var _this = this,
                nodes = (nodes instanceof Array) ? nodes: [nodes];
            nodes.forEach(function(actor){
                _this.actors.add(actor);
            })
        },

        getNodes: function(){
            return this.actors.models;
        },

        getFlows: function(){
            return this.flows.models;
        },

        removeFlows: function(flows){
            var flows = (flows instanceof Array) ? flows: [flows];
            this.flows.remove(flows);
        },

        removeNodes: function(nodes, unusedOnly){
            var _this = this,
                nodes = (nodes instanceof Array) ? nodes: [nodes],
                usedNodes = new Set();
            if (unusedOnly) {
                this.flows.forEach(function(flow){
                    usedNodes.add(flow.get('origin'));
                    usedNodes.add(flow.get('destination'));
                })
            }
            nodes.forEach(function(node){
                if (!usedNodes.has(node.id))
                    _this.actors.remove(node);
            })
        },

        clear: function(){
            this.actors.reset();
            this.flows.reset();
            this.legend.innerHTML = '';
            this.data = null;
            this.clusterGroups = {};
            this.flowMap.clear();
        },

        prefetchLocations: function(callback){
            var nodeIds = [],
                _this = this;
            var adminLocations = new GeoLocations([], {
                apiTag: 'adminLocations',
                apiIds: [this.caseStudyId, this.keyflowId]
            });
            this.actors.forEach(function(actor){
                if (actor.id in _this.locations) return;
                nodeIds.push(actor.id);
            })
            if(nodeIds.length === 0) callback();
            else {
                var data = {};
                data['actor__in'] = nodeIds.join(',');
                adminLocations.postfetch({
                    body: data,
                    success: function(){
                        adminLocations.forEach(function(adminLoc){
                            id = adminLoc.get('properties').actor;
                            _this.locations[id] = adminLoc;
                        })
                        callback();
                    }
                });
            }

        },

        transformMarkerClusterData: function(){
            var clusters = [];
            Object.values(this.clusterGroups).forEach(function(clusterGroup){
                clusterGroup.instance._featureGroup.eachLayer(function(layer) {
                    if (layer instanceof L.MarkerCluster) {
                        var point = layer.getLatLng(),
                            cluster = {
                            ids: [],
                            color: clusterGroup.color,
                            label: clusterGroup.label,
                            lat: point.lat,
                            lon: point.lng
                        }
                        layer.getAllChildMarkers().forEach(function(marker){
                            cluster.ids.push(marker.id);
                        })
                        clusters.push(cluster);
                    }
                });
            })
            data = this.transformData(
                this.actors, this.flows, this.locations,
                {
                    splitByComposition: this.materialCheck.checked,
                    clusters: clusters
                }
            );
            return data;
        },

        /*
        * transform actors and flows to a json-representation
        * readable by the sankey-diagram
        *
        * options.splitByComposition - split flows by their compositions (aka materials) into seperate flows
        * options.clusters - array of objects with keys "lat", "lon" (location) and "ids" (array of actor ids that belong to that cluster)
        */
        transformData: function(actors, flows, locations, options) {

            var _this = this,
                options = options || {},
                nodes = {},
                links = [],
                clusters = options.clusters || [],
                splitByComposition = options.splitByComposition,
                clusterMap = {},
                pFlows = [],
                warnings = [];

            var i = 0;
            clusters.forEach(function(cluster){
                var nNodes = cluster.ids.length,
                    clusterId = 'cluster' + i,
                    label = cluster.label + ' (' + nNodes + ' ' + gettext('actors') + ')';
                var clusterNode = {
                    id: clusterId,
                    name: label,
                    label: label,
                    color: cluster.color,
                    lon: cluster.lon,
                    lat: cluster.lat,
                    radius: Math.min(40, 15 + nNodes / 2),
                    innerLabel: nNodes,
                    cluster: cluster
                }
                nodes[clusterId] = clusterNode;
                i++;
                cluster.ids.forEach(function(id){
                    clusterMap[id] = clusterId;
                })
            })

            actors.forEach(function(actor){
                // actor is clustered
                if (clusterMap[actor.id]) return;

                var location = _this.locations[actor.id];
                if (!location || !location.get('geometry')) {
                    var warning = gettext('Actor referenced by flow, but missing a location:') + ' ' + actor.get('name');
                    warnings.push(warning);
                    return;
                }
                var location = _this.locations[actor.id],
                    geom = location.get('geometry');
                if (!geom) return;

                var coords = geom.get('coordinates'),
                    lon = coords[0],
                    lat = coords[1];
                var transNode = {
                    id: actor.id,
                    name: actor.get('name'),
                    label: actor.get('name'),
                    color: actor.color,
                    group: actor.group,
                    lon: lon,
                    lat: lat,
                    radius: 10
                }
                nodes[actor.id] = transNode;
            });

            // aggregate flows
            Object.values(nodes).forEach(function(source){
                Object.values(nodes).forEach(function(target){
                    // source and target are same or none of them is clustered
                    if(source === target || (!source.cluster && !target.cluster)) return;
                    var originIds = (source.cluster) ? source.cluster.ids : [source.id],
                        destIds = (target.cluster) ? target.cluster.ids : target.id;
                    var outFlows = flows.filterBy({origin: originIds, destination: destIds});
                    if (outFlows.length > 0){
                        aggregated = outFlows.aggregate();
                        aggregated.set('origin', source.id);
                        aggregated.set('destination', target.id);
                        pFlows.push(aggregated);
                    }
                })
            })

            // add the flows that don't have to be aggregated, because origin and destination are not clustered
            flows.forEach(function(flow) {
                var originId = flow.get('origin'),
                    destId = flow.get('destination');
                if (!clusterMap[originId] && !clusterMap[destId]){
                    // nodes might have no geometry and skipped, don't add flow then
                    if(!nodes[originId] || !nodes[destId]) return;
                    pFlows.push(flow);
                }
            })

            var uniqueMaterials = new Set(),
                matColors = {};

            pFlows.forEach(function(flow) {
                var sourceId = flow.get('origin'),
                    targetId = flow.get('destination');
                var sourceNode = nodes[sourceId],
                    targetNode = nodes[targetId],
                    composition = flow.get('composition');

                var wasteLabel = (flow.get('waste')) ? '<b>Waste</b>' : '<b>Product</b>',
                    totalAmount = Math.round(flow.get('amount')),
                    flowLabel = sourceNode.name + '&#10132; '  + targetNode.name + '<br>' + wasteLabel;;

                if(splitByComposition){
                    composition.fractions.forEach(function(fraction){
                        var material = _this.materials.get(fraction.material),
                            amount = Math.round(totalAmount * fraction.fraction),
                            label = flowLabel + ': ' + composition.name + '<br><b>Material: </b>' + material.get('name') + '<br><b>Amount: </b>' + _this.format(amount) + ' t/year';
                        links.push({
                            id: flow.id,
                            label: label,
                            source: sourceId,
                            target: targetId,
                            value: amount,
                            material: material.id,
                            tag: material.id
                        })
                        uniqueMaterials.add(material.id);
                    })
                    //define colors for individual materials and store in styles
                    //var materialColor = d3.scale.linear()
                        //.range (["#4477AA", "#66CCEE","#228833","#CCBB44","#EE6677","#AA3377"])
                        //.domain([0, 1/5*(uniqueMaterials.size-1), 2/5*(uniqueMaterials.size-1), 3/5*(uniqueMaterials.size-1), 4/5*(uniqueMaterials.size-1), (uniqueMaterials.size-1)])
                        //.interpolate(d3.interpolateHsl);

                    var i = 0;
                    uniqueMaterials.forEach(function (materialId) {
                        var color = utils.colorByName(_this.materials.get(materialId).get('name'));
                        matColors[materialId] = color;
                        i++;
                    });

                    links.forEach(function(link){
                        link.color = matColors[link.material];
                    })
                }
                else {
                    var label = flowLabel + '<br><b>Amount: </b>' + _this.format(totalAmount) + ' t/year';
                    links.push({
                        id: flow.id,
                        label: label,
                        source: flow.get('origin'),
                        target: flow.get('destination'),
                        color: sourceNode.color,
                        value: totalAmount
                    })
                }
            })

            return {
                flows: links,
                nodes: Object.values(nodes),
                materialColors: matColors,
                warnings: warnings
            }
        }

    });
    return FlowSankeyMapView;
}
);
