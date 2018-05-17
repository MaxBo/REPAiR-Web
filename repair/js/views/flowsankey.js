define(['views/baseview', 'underscore', 'visualizations/sankey', 
    'collections/gdsecollection'],

function(BaseView, _, Sankey, GDSECollection){

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
        * render view to edit flows of a single keyflow
        *
        * @param {Object} options
        * @param {HTMLElement} options.el                   element the view will be rendered in
        * @param {String} options.tag                       'actors', 'activities' or 'activitygroups', by default the apiTag of the collection is taken 
        * @param {Number=} options.width                    width of sankey diagram (defaults to width of el)
        * @param {Number=} options.height                   height of sankey diagram (defaults to 1/3 of width)
        * @param {Number=} options.caseStudyId              id of the casestudy
        * @param {Number=} options.keyflowId                id of the keyflow
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
            var _this = this;
            this.caseStudyId = options.caseStudyId;
            this.keyflowId = options.keyflowId;
            this.materials = options.materials;
            this.hideUnconnected = options.hideUnconnected;
            this.width = options.width || this.el.clientWidth;
            this.height = options.height || this.width / 3;
            var tag = options.tag || this.collection.apiTag

            var flowTag = (tag == 'actors') ? 'actorToActor': 
                          (tag == 'activities') ? 'activityToActivity':
                          'groupToGroup',
                stockTag = (tag == 'actors') ? 'actorStock': 
                           (tag == 'activities') ? 'activityStock':
                           'groupStock';
                
            this.flows = new GDSECollection([], {
                apiTag: flowTag,
                apiIds: [ this.caseStudyId, this.keyflowId] 
            });
            this.stocks = new GDSECollection([], {
                apiTag: stockTag,
                apiIds: [ this.caseStudyId, this.keyflowId] 
            });

            var fullscreenBtn = document.createElement('button');
            fullscreenBtn.classList.add("glyphicon", "glyphicon-fullscreen", "btn", "btn-primary", "fullscreen-toggle");
            fullscreenBtn.addEventListener('click', this.toggleFullscreen);
            this.el.appendChild(fullscreenBtn);

            this.loader.activate();
            var promises = [
                this.stocks.fetch({data: options.stockFilterParams}), 
                this.flows.fetch({data: options.flowFilterParams})
            ]
            Promise.all(promises).then(function(){
                _this.loader.deactivate();
                _this.render();
            });
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
        render: function(){
            this.sankeyData = this.transformData(this.collection, this.flows, this.stocks, this.materials);
            var isFullScreen = this.el.classList.contains('fullscreen');
            var width = (isFullScreen) ? this.el.clientWidth : this.width;
            var height = (isFullScreen) ? this.el.clientHeight : this.height;
            var div = this.el.querySelector('.sankey');
            if (div == null){
                div = document.createElement('div');
                div.classList.add('sankey', 'bordered');
                this.el.appendChild(div);
            }
            var sankey = new Sankey({
                height: height,
                width: width,
                el: div,
                title: ''
            })
            sankey.render(this.sankeyData);
        },

        /*
        * render sankey-diagram in fullscreen
        */
        toggleFullscreen: function(){
            this.el.classList.toggle('fullscreen');
            this.render();
        },

        refresh: function(options){
            var options = options || {};
            this.width = options.width || this.el.clientWidth;
            this.height = options.height || this.width / 3;
            this.render();
        },

        /*
        * transform the models, their links and the stocks to a json-representation
        * readable by the sankey-diagram
        */
        transformData: function(models, flows, stocks, materials){
            var _this = this;
            var nodes = [];
            var nodeIdxDict = {}
            var i = 0;
            
            function nConnectionsTo(connections, nodeId, options){
                var options = options || {},
                    filtered = (options.areStocks) ? connections.filterBy({ origin: nodeId }):
                               connections.filterBy({ origin: nodeId, destination: nodeId }, { operator: '||' });
                return filtered.length
            }

            models.forEach(function(model){
                var id = model.id;
                var name = model.get('name');
                // ignore nodes with no connections at all (if requested)
                if (_this.hideUnconnected) {
                    if (nConnectionsTo(flows, id) == 0 && 
                        nConnectionsTo(stocks, id, { areStocks: true }) == 0)
                        return;
                }
                nodes.push({ id: id, name: name });
                nodeIdxDict[id] = i;
                i += 1;
            });
            var links = [];

            function compositionRepr(composition){
                var text = '';
                if (composition){
                    var fractions = composition.fractions;
                    var i = 0;
                    fractions.forEach(function(fraction){
                        var material = materials.get(fraction.material);
                        text += fraction.fraction * 100 + '% ';
                        if (!material) text += gettext('material not found');
                        else text += material.get('name');
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
                    source = nodeIdxDict[originId],
                    target = nodeIdxDict[destinationId];
                // continue if one of the linked nodes does not exist
                if (source == null || target == null) return false;
                var composition = flow.get('composition');
                links.push({
                    value: flow.get('amount'),
                    units: gettext('t/year'),
                    source: source,
                    target: target,
                    text: typeRepr(flow) + '<br>' + compositionRepr(composition)
                });
            })
            stocks.forEach(function(stock){
                var id = 'stock-' + stock.id;
                var originId = stock.get('origin'),
                    source = nodeIdxDict[originId];
                // continue if node does not exist
                if (source == null) return false;
                nodes.push({id: id, name: 'Stock', alignToSource: {x: 80, y: 0}});
                var composition = stock.get('composition');
                links.push({
                    value: stock.get('amount'),
                    units: gettext('t/year'),
                    source: source,
                    target: i,
                    text: typeRepr(stock) + '<br>' + compositionRepr(composition)
                });
                i += 1;
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