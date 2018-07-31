define(['views/baseview', 'underscore', 'visualizations/sankey', 
        'collections/gdsecollection', 'd3', 'app-config'],

function(BaseView, _, Sankey, GDSECollection, d3, config){

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
            _.bindAll(this, 'clickHandler');
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
            var originTag = options.originLevel || this.origins.apiTag,
                destinationTag = options.destinationLevel || this.destinations.apiTag,
                renderStocks = (options.renderStocks != null) ? options.renderStocks : true;
            this.originAggregateLevel = (originTag.includes('group')) ? 'activitygroup': 
                                        (originTag.includes('actor')) ? 'actor': 'activity';
            this.destinationAggregateLevel = (destinationTag.includes('group')) ? 'activitygroup': 
                                             (destinationTag.includes('actor')) ? 'actor': 'activity';

            flowFilterParams = options.flowFilterParams || {};
            flowFilterParams['aggregation_level'] = {
                origin: this.originAggregateLevel,
                destination: this.destinationAggregateLevel
            };
            stockFilterParams = options.stockFilterParams || {};
            stockFilterParams['aggregation_level'] = this.originAggregateLevel;
            
            this.flows = new GDSECollection([], {
                apiTag: 'actorToActor',
                apiIds: [ this.caseStudyId, this.keyflowId] 
            });
            this.stocks = new GDSECollection([], {
                apiTag: 'actorStock',
                apiIds: [ this.caseStudyId, this.keyflowId] 
            });
            
            var fullscreenBtn = document.createElement('button'),
                zoomControls = document.createElement('div'),
                zoomIn = document.createElement('a'),
                inSpan = document.createElement('span'),
                zoomOut = document.createElement('a'),
                outSpan = document.createElement('span'),
                zoomToFit = document.createElement('a'),
                fitSpan = document.createElement('span');
                
            fullscreenBtn.classList.add("glyphicon", "glyphicon-fullscreen", "btn", "btn-primary", "fullscreen-toggle");
            
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
            
            fullscreenBtn.addEventListener('click', this.toggleFullscreen);

            this.loader.activate();
            var promises = [
                this.flows.postfetch({body: flowFilterParams})
            ]
            if (renderStocks){
                promises.push(this.stocks.postfetch({body: stockFilterParams}));
            }
            Promise.all(promises).then(function(){
                _this.complementData(function(data){
                    _this.transformedData = data;
                    _this.loader.deactivate();
                    _this.render(data);
                })
            });
            this.onClick = options.onClick;
        },

        /*
        * dom events (managed by jquery)
        */
        events: {
            'click a[href="#flow-map-panel"]': 'refreshMap',
            'change #data-view-type-select': 'renderSankey'
        },
        
        clickHandler: function(d){
            var flow = this.flows.get(d.id),
                origin = this.origins.get(d.source.id),
                destination = this.destinations.get(d.target.id);
            console.log(d)
            origin.color = d.source.color;
            destination.color = d.target.color;
            this.onClick(flow, origin, destination);
        },
        
        complementData: function(success){
            var originIds = this.origins.pluck('id'),
                destinationIds = this.destinations.pluck('id'),
                missingOriginIds = new Set(),
                missingDestinationIds = new Set(),
                _this = this;
            this.flows.forEach(function(flow){
                var origin = flow.get('origin'),
                    destination = flow.get('destination');
                if(!originIds.includes(origin)) missingOriginIds.add(origin);
                if(!destinationIds.includes(destination)) missingDestinationIds.add(destination);
            })
            
            function getUrl(tag){
                var url = (tag.includes('group')) ? config.api.activitygroups:
                          (tag.includes('actor')) ? config.api.actors:
                          config.api.activities;
                return url.format(_this.caseStudyId, _this.keyflowId);
            }
            var promises = [];
            // WARNING: postfetch works only with filter actors route, should be
            // fetched in case of groups and activities, but in fact they should
            // be complete
            if (missingOriginIds.size > 0){
                var missingOrigins = new GDSECollection([], {
                    url: getUrl(this.originAggregateLevel)
                })
                promises.push(missingOrigins.postfetch({ 
                    body: { 'id': Array.from(missingOriginIds).join() },
                    success: function(){
                        _this.origins.add(missingOrigins.toJSON(), {silent: true});
                    }
                }))
            }
            if (missingDestinationIds.size > 0){
                var missingDestinations = new GDSECollection([], {
                    url: getUrl(this.destinationAggregateLevel)
                })
                promises.push(missingDestinations.postfetch({ 
                    body: { 'id': Array.from(missingDestinationIds).join() },
                    success: function(){
                        _this.destinations.add(missingDestinations.toJSON(), {silent: true});
                    }
                }))
            }
            
            Promise.all(promises).then(function(){
                var data = _this.transformData(
                    _this.origins, _this.destinations, _this.flows, _this.stocks, _this.materials);
                success(data);
            })
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
            var sankey = new Sankey({
                height: height,
                width: width,
                el: div,
                title: '',
                language: config.session.get('language'),
                onClick: this.clickHandler
            })
            if (data.nodes.length == 0)
                _this.el.innerHTML = gettext("No flow data found for applied filters.")
            else sankey.render(data);
        },

        /*
        * render sankey-diagram in fullscreen
        */
        toggleFullscreen: function(){
            this.el.classList.toggle('fullscreen');
            this.render(this.transformedData);
        },

        refresh: function(options){
            var options = options || {};
            this.width = options.width || this.el.clientWidth;
            this.height = options.height || this.width / 3;
            this.render();
        },
        
        format: function(value){
            return value.toLocaleString(this.language);
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
            var sourcePrefix = (this.forceSideBySide) ? 'origin': this.originAggregateLevel,
                targetPrefix = (this.forceSideBySide) ? 'destination': this.destinationAggregateLevel;
            
            function checkOrigins(id){ return nConnectionsOut(flows, id) + nConnectionsOut(stocks, id) > 0 }
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
                    destinationId = flow.get('destination'),
                    source = indices[sourcePrefix+originId],
                    target = indices[targetPrefix+destinationId];
                // continue if one of the linked nodes does not exist
                if (source == null || target == null) return false;
                var composition = flow.get('composition');
                links.push({
                    id: flow.id,
                    value: flow.get('amount'),
                    units: gettext('t/year'),
                    source: source,
                    target: target,
                    isStock: false,
                    text: '<u>' + typeRepr(flow) + '</u><br>' + compositionRepr(composition)
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
                var composition = stock.get('composition');
                links.push({
                    id: stock.id,
                    isStock: true,
                    value: stock.get('amount'),
                    units: gettext('t/year'),
                    source: source,
                    target: idx,
                    text: typeRepr(stock) + '<br>' + compositionRepr(composition)
                });
                idx += 1;
            });

            var transformed = {nodes: nodes, links: links};
            return transformed;
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