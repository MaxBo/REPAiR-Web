define(['views/common/baseview', 'underscore', 'visualizations/sankey',
        'collections/gdsecollection', 'd3', 'app-config', 'save-svg-as-png',
        'file-saver'],

function(BaseView, _, Sankey, GDSECollection, d3, config, saveSvgAsPng,
         FileSaver){

    /**
    *
    * @author Christoph Franke
    * @name module:views/FlowSankeyView
    * @augments module:views/BaseView
    */
    var FlowSankeyView = BaseView.extend(
        /** @lends module:views/FlowSankeyView.prototype */
        {

        /**
        * render flows in sankey diagram
        *
        * @param {Object} options
        * @param {HTMLElement} options.el                   element the view will be rendered in
        * @param {Backbone.Collection} options.origins      origins
        * @param {Backbone.Collection} options.destinations destinations
        * @param {Number=} options.width                    width of sankey diagram (defaults to width of el)
        * @param {Number=} options.height                   height of sankey diagram (defaults to 1/3 of width)
        * @param {Number} options.caseStudyId               id of the casestudy
        * @param {Number} options.keyflowId                 id of the keyflow
        * @param {Backbone.Collection} options.materials    materials
        * @param {boolean=} [options.renderStocks=true]     if false, stocks won't be rendered
        * @param {boolean=} [options.forceSideBySide=false] if true, the network of flows will be represented with sinks and sources only, nodes in between (meaning nodes with in AND out flows) will be split into a sink and source
        * @param {Object=} options.flowFilterParams         parameters to filter the flows with (e.g. {material: 1})
        * @param {Object=} options.stockFilterParams        parameters to filter the stocks with
        * @param {boolean} [options.hideUnconnected=false]  hide nodes that don't have in or outgoing flows or stocks (filtered by filterParams)
        * @param {module:collections/GDSECollection}        options.collection the nodes to render
        *
        * @constructs
        * @see http://backbonejs.org/#View
        */
        initialize: function(options){
            FlowSankeyView.__super__.initialize.apply(this, [options]);
            _.bindAll(this, 'toggleFullscreen');
            _.bindAll(this, 'exportPNG');
            _.bindAll(this, 'exportCSV');
            var _this = this;
            this.language = config.session.get('language');
            this.caseStudyId = options.caseStudyId;
            this.keyflowId = options.keyflowId;
            this.materials = options.materials;
            this.hideUnconnected = options.hideUnconnected;
            this.width = options.width || this.el.clientWidth;
            this.height = options.height || this.width / 3;
            this.forceSideBySide = options.forceSideBySide || false;
            this.origins = options.origins;
            this.destinations = options.destinations;
            this.flows = options.flows;
            this.stocks = options.stocks || [];

            var fullscreenBtn = document.createElement('button'),
                exportImgBtn = document.createElement('button'),
                exportCsvBtn = document.createElement('button'),
                zoomControls = document.createElement('div'),
                zoomIn = document.createElement('a'),
                inSpan = document.createElement('span'),
                zoomOut = document.createElement('a'),
                outSpan = document.createElement('span'),
                zoomToFit = document.createElement('a'),
                fitSpan = document.createElement('span');

            fullscreenBtn.classList.add("fas", "fa-expand", "btn", "btn-primary", "fullscreen-toggle", "d3-overlay");
            exportImgBtn.classList.add("fas", "fa-camera", "btn", "btn-primary", "d3-overlay", "inverted");
            exportImgBtn.style.top = "100px";
            exportImgBtn.style.right = "20px";
            exportImgBtn.style.height = "30px";
            exportCsvBtn.classList.add("fas", "fa-file", "btn", "btn-primary", "d3-overlay", "inverted");
            exportCsvBtn.style.top = "140px";
            exportCsvBtn.style.right = "20px";
            exportCsvBtn.style.height = "30px";

            zoomIn.classList.add("btn", "square");
            zoomIn.setAttribute('data-zoom', "+0.5");
            inSpan.classList.add("fa", "fa-plus");
            zoomIn.appendChild(inSpan);

            zoomOut.classList.add("btn", "square");
            zoomOut.setAttribute('data-zoom', "-0.5");
            outSpan.classList.add("fa", "fa-minus");
            zoomOut.appendChild(outSpan);

            zoomToFit.classList.add("btn", "square");
            zoomToFit.setAttribute('data-zoom', "0");
            fitSpan.classList.add("fa", "fa-crosshairs");
            zoomToFit.appendChild(fitSpan);

            zoomControls.classList.add("d3-zoom-controls");
            zoomControls.appendChild(zoomIn);
            zoomControls.appendChild(zoomOut);
            zoomControls.appendChild(zoomToFit);

            this.el.appendChild(zoomControls);
            this.el.appendChild(fullscreenBtn);
            this.el.appendChild(exportImgBtn);
            this.el.appendChild(exportCsvBtn);

            fullscreenBtn.addEventListener('click', this.toggleFullscreen);
            exportImgBtn.addEventListener('click', this.exportPNG);
            exportCsvBtn.addEventListener('click', this.exportCSV);

            this.transformedData = this.transformData(
                this.origins, this.destinations, this.flows,
                this.stocks, this.materials
            );
            this.render(this.transformedData);
            this.onSelect = options.onSelect;
            this.onDeselect = options.onDeselect;
        },

        /*
        * dom events (managed by jquery)
        */
        events: {
            'click a[href="#flow-map-panel"]': 'refreshMap',
            'change #data-view-type-select': 'renderSankey'
        },

        /*
        * render the view
        */
        render: function(data){
            var isFullScreen = this.el.classList.contains('fullscreen'),
                width = (isFullScreen) ? this.el.clientWidth : this.width,
                height = (isFullScreen) ? this.el.clientHeight : this.height,
                div = this.el.querySelector('.sankey'),
                _this = this;
            if (div == null){
                div = document.createElement('div');
                div.classList.add('sankey', 'bordered');
                this.el.appendChild(div);
            }
            this.sankeyDiv = div;
            this.sankey = new Sankey({
                height: height,
                width: width,
                el: div,
                title: '',
                language: config.session.get('language'),
                selectable: true,
                gradient: false
            })

            // get models from sankey data and redirect the event
            function redirectEvent(e){
                var d = e.detail,
                    flow = _this.flows.get(d.id),
                    origin = _this.origins.get(d.source.id),
                    destination = _this.destinations.get(d.target.id);
                origin.color = d.source.color;
                destination.color = d.target.color;
                _this.el.dispatchEvent(new CustomEvent( e.type, { detail: {
                    flow: flow,
                    origin: origin,
                    destination: destination
                }}))
            }

            div.addEventListener('linkSelected', redirectEvent);
            div.addEventListener('linkDeselected', redirectEvent);
            if (data.links.length === 0)
                _this.el.innerHTML = gettext("No flow data found for applied filters.")
            else this.sankey.render(data);
        },

        /*
        * render sankey-diagram in fullscreen
        */
        toggleFullscreen: function(){
            this.el.classList.toggle('fullscreen');
            this.refresh()
            //this.render(this.transformedData);
        },

        refresh: function(options){
            var isFullScreen = this.el.classList.contains('fullscreen'),
                options = options || {},
                width = (isFullScreen) ? this.el.clientWidth : (options.width) ? options.width : this.width,
                height = (isFullScreen) ? this.el.clientHeight : (options.height) ? options.height : this.height;
            this.sankey.setSize(width, height);
            this.sankey.zoomToFit();
        },

        /*
        * transform the models, their links and the stocks to a json-representation
        * readable by the sankey-diagram
        */
        transformData: function(origins, destinations, flows, stocks, materials){
            var _this = this,
                nodes = [],
                indices = {},
                labels = {},
                colorCat = d3.scale.category20();

            function nConnectionsInOut(connections, nodeId){
                return connections.filterBy({ origin: nodeId, destination: nodeId }, { operator: '||' }).length;
            }

            function nConnectionsIn(connections, nodeId){
                return connections.filterBy({ destination: nodeId }).length;
            }

            function nConnectionsOut(connections, nodeId){
                if (connections.length === 0) return 0;
                return connections.filterBy({ origin: nodeId }).length;
            }

            var idx = 0;

            function addNodes(collection, prefix, check){
                collection.forEach(function(model){
                    var id = model.id,
                        name = model.get('name');
                    // we already got this one -> skip it
                    if(indices[prefix+id] != null) return;
                    // no connections -> skip it (if requested)
                    if (_this.hideUnconnected && !check(id)) return;

                    var color = colorCat(name.replace(/ .*/, ""));
                    nodes.push({ id: id, name: name, color: color });
                    indices[prefix+id] = idx;
                    labels[prefix+id] = model.get('name');
                    idx += 1;
                });
            }
            var sourcePrefix = (this.forceSideBySide) ? 'origin': origins.apiTag,
                targetPrefix = (this.forceSideBySide) ? 'destination': destinations.apiTag;

            function checkOrigins(id){
                return nConnectionsOut(flows, id) + nConnectionsOut(stocks, id) > 0
            }
            addNodes(origins, sourcePrefix, checkOrigins);
            function checkDestinations(id){ return nConnectionsIn(flows, id) > 0 }
            addNodes(destinations, targetPrefix, checkDestinations);
            var links = [];

            function compositionRepr(composition){
                var text = '';
                if (composition){
                    var fractions = composition.fractions;
                    var i = 0;
                    fractions.forEach(function(fraction){
                        var material = materials.get(fraction.material),
                            value = Math.round(fraction.fraction * 100000) / 1000
                        text += _this.format(value) + '% ';
                        if (!material) text += gettext('material not found');
                        else text += material.get('name');
                        if (fraction.avoidable) text += ' <i>' + gettext('avoidable') +'</i>';
                        if (i < fractions.length - 1) text += '<br>';
                        i++;
                    })
                }
                return text || ('no composition defined');
            }

            function typeRepr(flow){
                return flow.get('waste') ? 'Waste': 'Product';
            }

            flows.forEach(function(flow){
                var value = flow.get('amount');
                var originId = flow.get('origin'),
                    destinationId = flow.get('destination');
                if (originId == destinationId) {
                    console.log('Warning: self referencing cycle at node id ' + originId);
                    return;
                }
                var source = indices[sourcePrefix+originId],
                    target = indices[targetPrefix+destinationId];
                // continue if one of the linked nodes does not exist
                if (source == null || target == null) return false;
                var composition = flow.get('composition'),
                    crepr = compositionRepr(composition);
                links.push({
                    id: flow.id,
                    value: flow.get('amount'),
                    units: gettext('t/year'),
                    source: source,
                    target: target,
                    isStock: false,
                    text: '<u>' + typeRepr(flow) + '</u><br>' + crepr,
                    composition: crepr.replace(new RegExp('<br>', 'g'), ' | ')
                });
            })
            stocks.forEach(function(stock){
                var id = 'stock-' + stock.id;
                var originId = stock.get('origin'),
                    source = indices[sourcePrefix+originId],
                    sourceName = labels[sourcePrefix+originId];
                // continue if node does not exist
                if (source == null) return false;
                nodes.push({id: id, name: 'Stock ',
                            text: sourceName,
                            color: 'darkgray',
                            alignToSource: {x: 80, y: 0}});
                var composition = stock.get('composition'),
                    crepr = compositionRepr(composition);
                links.push({
                    id: stock.id,
                    isStock: true,
                    value: stock.get('amount'),
                    units: gettext('t/year'),
                    source: source,
                    target: idx,
                    text: typeRepr(stock) + '<br>' + crepr,
                    composition: crepr.replace(new RegExp('<br>', 'g'), ' | ')
                });
                idx += 1;
            });

            var transformed = {nodes: nodes, links: links};
            return transformed;
        },

        exportPNG: function(){
            var svg = this.sankeyDiv.querySelector('svg');
            saveSvgAsPng.saveSvgAsPng(svg, "sankey-diagram.png", {scale: 2, backgroundColor: "#FFFFFF"});
        },

        exportCSV: function(){
            if (!this.transformedData) return;

            var header = [gettext('origin'), gettext('destination'), gettext('amount'), gettext('composition')],
                rows = [],
                _this = this;
            rows.push(header.join('\t'));
            this.transformedData.links.forEach(function(link){
                var origin = link.source.name,
                    destination = (!link.isStock) ? link.target.name : gettext('Stock'),
                    amount = _this.format(link.value) + ' ' + link.units,
                    composition = link.composition;
                var row = [origin, destination, amount, composition];
                rows.push(row.join('\t'));
            });
            var text = rows.join('\r\n');
            var blob = new Blob([text], {type: "text/plain;charset=utf-8"});
            FileSaver.saveAs(blob, "data.csv");
        },

        /*
        * remove this view from the DOM
        */
        close: function(){
            this.undelegateEvents(); // remove click events
            this.unbind(); // Unbind all local event bindings
            this.el.innerHTML = ''; //empty the DOM element
        },

    });
    return FlowSankeyView;
}
);
