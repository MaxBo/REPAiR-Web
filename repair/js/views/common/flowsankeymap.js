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

            this.locations = {};
            this.flows = new Flows();
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
                center = [52.51, 13.36];
            if (focusarea){
                var poly = new ol.geom.MultiPolygon(focusarea.coordinates),
                    interior = poly.getInteriorPoints(),
                    centroid = interior.getCoordinates()[0];
                    center = [centroid[1], centroid[0]];
            }

            this.leafletMap = new L.Map(this.el, {
                    center: center,
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
            this.stockCheck = document.createElement('input');
            this.flowCheck = document.createElement('input');
            this.flowCheck.checked = true;
            this.stockCheck.checked = true;

            var div = document.createElement('div'),
                matLabel = document.createElement('label'),
                aniLabel = document.createElement('label'),
                actorLabel = document.createElement('label'),
                stockLabel = document.createElement('label'),
                flowLabel = document.createElement('label'),
                clusterLabel = document.createElement('label'),
                _this = this;

            matLabel.innerHTML = gettext('Display materials');
            aniLabel.innerHTML = gettext('Animate flows');
            clusterLabel.innerHTML = gettext('Cluster locations');
            actorLabel.innerHTML = gettext('Show actors');
            flowLabel.innerHTML = gettext('Show flows');
            stockLabel.innerHTML = gettext('Show stocks');

            [
                this.materialCheck, this.clusterCheck,
                this.animationCheck, this.actorCheck,
                this.flowCheck, this.stockCheck
            ].forEach(function(checkbox){
                checkbox.type = "checkbox";
                checkbox.style.transform = "scale(2)";
                checkbox.style.pointerEvents = "none";
                checkbox.style.marginRight = "10px";
            })

            div.style.background = "rgba(255, 255, 255, 0.5)";
            div.style.padding = "10px";
            div.style.cursor = "pointer";

            var matDiv = document.createElement('div'),
                actorDiv = document.createElement('div'),
                stockDiv = document.createElement('div'),
                flowDiv = document.createElement('div'),
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
            stockDiv.appendChild(this.stockCheck);
            stockDiv.appendChild(stockLabel);
            stockDiv.style.cursor = 'pointer';
            flowDiv.appendChild(this.flowCheck);
            flowDiv.appendChild(flowLabel);
            flowDiv.style.cursor = 'pointer';
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

            flowDiv.addEventListener("click", function(){
                _this.flowCheck.checked = !_this.flowCheck.checked;
                _this.rerender();
            });
            stockDiv.addEventListener("click", function(){
                _this.stockCheck.checked = !_this.stockCheck.checked;
                if (_this.stockCheck.checked) _this.actorCheck.checked = false;
                _this.rerender();
            });
            actorDiv.addEventListener("click", function(){
                _this.actorCheck.checked = !_this.actorCheck.checked;
                if (_this.actorCheck.checked) _this.stockCheck.checked = false;
                _this.rerender();
            });
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

            div.appendChild(flowDiv);
            div.appendChild(document.createElement('br'));
            div.appendChild(stockDiv);
            div.appendChild(document.createElement('br'));
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
            var materials = data.materials;
            // ToDo: inefficient, done too often for just toggling visibility
            Object.keys(materials).forEach(function(matId){
                var material = materials[matId],
                    color = material.color,
                    div = document.createElement('div'),
                    text = document.createElement('div'),
                    check = document.createElement('input'),
                    colorDiv = document.createElement('div');
                div.style.height = '25px';
                div.style.cursor = 'pointer';
                text.innerHTML = material.name;
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
                    _this.rerender();
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

            if (this.stockCheck.checked)
                this.flowMap.addNodes(data.stocks);
            if (this.flowCheck.checked)
                this.flowMap.addFlows(data.flows);
            //this.flowMap.showNodes = (this.actorCheck.checked) ? true: false;
            this.flowMap.showFlows = (this.flowCheck.checked) ? true: false;
            this.flowMap.dottedLines = (this.aniDotsRadio.checked) ? true: false;
            this.updateLegend();
            this.flowMap.toggleTag('actor', this.actorCheck.checked);

            this.flowMap.resetView();
            //if (zoomToFit) this.flowMap.zoomToFit();
        },

        rerender: function(zoomToFit){
            var _this = this;
            var splitByComposition = _this.materialCheck.checked;
            var data = _this.transformData(
                _this.flows,
                {
                    splitByComposition: splitByComposition
                }
            );
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
        },

        /*
        additional to the usual attributes the flow should have the attribute
        'color'
        */
        addFlows: function(flows){
            var _this = this;
                flows = (flows.forEach != null) ? flows: [flows];
            flows.forEach(function(flow){
                _this.flows.add(flow);
            })
        },

        getFlows: function(){
            return this.flows.models;
        },

        removeFlows: function(flows){
            var flows = (flows instanceof Array) ? flows: [flows];
            this.flows.remove(flows);
        },

        clear: function(){
            this.flows.reset();
            this.legend.innerHTML = '';
            this.data = null;
            this.clusterGroups = {};
            this.flowMap.clear();
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
                this.flows,
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
        transformData: function(flows, options) {

            var _this = this,
                options = options || {},
                nodes = {},
                links = [],
                clusters = options.clusters || [],
                splitByComposition = options.splitByComposition,
                clusterMap = {},
                pFlows = [],
                warnings = [],
                maxStock = 0;

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
                    cluster: cluster,
                    tag: 'actor'
                }
                nodes[clusterId] = clusterNode;
                i++;
                cluster.ids.forEach(function(id){
                    clusterMap[id] = clusterId;
                })
            })

            function transformNode(node){
                var id = node.id,
                    clusterId = clusterMap[id];

                // node already clustered
                if (clusterId != null) return nodes[clusterId];

                var name = node.name,
                    level = node.level,
                    key = level + id;
                if (!node.geom){
                    var warning = gettext('Actor referenced by flow, but missing a location:') + ' ' + name;
                    warnings.push(warning);
                    return;
                }
                var coords = node.geom.coordinates;
                var transNode = {
                    id: id,
                    name: name,
                    label: name,
                    color: node.color,
                    group: node.group,
                    lon: coords[0],
                    lat: coords[1],
                    radius: 10,
                    tag: 'actor'
                }
                nodes[id] = transNode;
                return transNode;
            }

            var aggMap = {};
            function aggregate(flow, source, target) {
                var key = flow.get('waste') + source.id,
                    is_stock = flow.get('stock');
                if (!is_stock) key += + '-' + target.id;
                var mapped = aggMap[key];
                // not
                if (!mapped){
                    mapped = {
                        id: key,
                        source: source,
                        target: target,
                        waste: flow.get('waste'),
                        amount: flow.get('amount'),
                        fractions: {},
                        is_stock: is_stock
                    }
                    fractions = mapped.fractions;
                    flow.get('materials').forEach(function(material){
                        fractions[material.material] = Object.assign({}, material);
                    })
                    aggMap[key] = mapped;
                    pFlows.push(mapped);
                }
                else {
                    fractions = mapped.fractions;
                    flow.get('materials').forEach(function(material){
                        var mat = fractions[material.material];
                        if (!mat){
                            mat = Object.assign({}, material);
                            fractions[material.material] = mat;
                        }
                        else
                            mat.amount += material.amount;
                    })
                    mapped.amount += flow.get('amount');
                }
            }

            i = 0;
            // add the flows that don't have to be aggregated, because origin and destination are not clustered
            flows.forEach(function(flow) {
                var origin = flow.get('origin'),
                    destination = flow.get('destination'),
                    is_stock = flow.get('stock'),
                    amount = flow.get('amount');

                var source = transformNode(origin),
                    target = (!is_stock) ? transformNode(destination): source; // set target to source in case of stocks just for convenience, doesn't matter

                if (is_stock)
                    maxStock = Math.max(maxStock, amount);

                // one node might have no geom (in case of stocks same node) -> cannot shown on map
                if(!source || !target) return;

                // one node is clustered (in case of stocks same node) -> aggregate
                if (source.cluster || target.cluster) {
                    aggregate(flow, source, target);
                }
                else {
                    pFlows.push({
                        id: flow.id || i,
                        source: source,
                        target: target,
                        is_stock: is_stock,
                        amount: amount,
                        fractions: flow.get('materials'),
                        waste: flow.get('waste')
                    });
                }
                i += 1;
            })
            var maxClusterStock = 0;
            // posproc the aggregation (just dict to list)
            Object.values(aggMap).forEach(function(flow){
                flow.fractions = Object.values(flow.fractions);
                if (flow.is_stock)
                    maxClusterStock = Math.max(maxClusterStock, flow.amount)
            })

            function transformFlow(pFlow){
                var source = pFlow.source,
                    target = pFlow.target,
                    fractions = pFlow.fractions;

                var wasteLabel = (pFlow.waste) ? 'Waste' : 'Product',
                    totalAmount = Math.round(pFlow.amount),
                    flowLabel = source.name + '&#10132; '  + target.name + '<br>' + wasteLabel;

                if(splitByComposition){
                    var cl = []
                    fractions.forEach(function(material){
                        var amount = Math.round(material.amount),
                            label = flowLabel + '<br><b>Material: </b>' + material.name + '<br><b>Amount: </b>' + _this.format(amount) + ' t/year',
                            color;
                        if (!uniqueMaterials[material.material]){
                            color = utils.colorByName(material.name)
                            uniqueMaterials[material.material] = {
                                color: color,
                                name: material.name
                            };
                        }
                        else
                            color = uniqueMaterials[material.material].color;
                        cl.push({
                            id: pFlow.id,
                            label: label,
                            source: source.id,
                            target: target.id,
                            value: amount,
                            material: material.material,
                            tag: material.material,
                            color: color
                        })
                    })
                    return cl;
                }
                else {
                    var label = flowLabel + '<br><b>Amount: </b>' + _this.format(totalAmount) + ' t/year';
                    return [{
                        id: pFlow.id,
                        label: label,
                        source: source.id,
                        target: target.id,
                        color: source.color,
                        value: totalAmount,
                        tag: 'flow'
                    }]
                }
            }

            function transformStock(pFlow){
                var source = pFlow.source,
                    fractions = pFlow.fractions;

                var wasteLabel = (pFlow.waste) ? 'Waste' : 'Product',
                    totalAmount = Math.round(pFlow.amount),
                    stockLabel = source.name + '<br>' + wasteLabel + ' ' + gettext('Stock'),
                    label = stockLabel + '<br><b>Amount: </b>' + _this.format(totalAmount) + ' t/year';

                var amount = pFlow.amount;

                // max radius 40 for unclustered stocks
                if (amount <= maxStock)
                    radius = 10 + 30 * amount / maxStock
                // amount exceeding maximum due to clustering -> reduce the exceeding sizes
                // to max radius 70
                else
                   radius = 40 + 30 * (amount - maxStock) / (maxClusterStock - maxStock);

                var stock = {
                    id: 'stock' + pFlow.id,
                    label: label,
                    color: source.color,
                    group: source.group,
                    lon: source.lon,
                    lat: source.lat,
                    radius: radius,
                    value: totalAmount,
                    tag: 'stock'
                }
                return stock;
            }

            var stocks = [];

            var uniqueMaterials = {};
            pFlows.forEach(function(pFlow) {
                if (!pFlow.is_stock){
                    links = links.concat(transformFlow(pFlow));
                }
                else
                    stocks.push(transformStock(pFlow));
            })

            return {
                flows: links,
                stocks: stocks,
                nodes: Object.values(nodes),
                materials: uniqueMaterials,
                warnings: warnings
            }
        }

    });
    return FlowSankeyMapView;
}
);
