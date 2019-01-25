define(['views/common/baseview', 'underscore', 'views/common/flowsankeymap',
        'collections/gdsecollection', 'views/common/flowsankey', 'utils/utils'],

function(BaseView, _, FlowMapView, GDSECollection,
         FlowSankeyView, utils){
/**
*
* @author Christoph Franke
* @name module:views/FlowsView
* @augments module:views/BaseView
*/
var FlowsView = BaseView.extend(
    /** @lends module:views/FlowsView.prototype */
    {

    /**
    * render flows filtered by given filter on map and in sankey
    *
    * @param {Object} options
    * @param {HTMLElement} options.el                     element the view will be rendered in
    * @param {string} options.template                    id of the script element containing the underscore template to render this view
    * @param {module:models/CaseStudy} options.caseStudy  the casestudy to add layers to
    *
    * @constructs
    * @see http://backbonejs.org/#View
    */
    initialize: function(options){
        var _this = this;
        FlowsView.__super__.initialize.apply(this, [options]);
        _.bindAll(this, 'linkSelected');
        _.bindAll(this, 'linkDeselected');
        _.bindAll(this, 'selectAll');
        _.bindAll(this, 'deselectAll');

        this.template = options.template;
        this.caseStudy = options.caseStudy;
        this.keyflowId = options.keyflowId;
        this.materials = options.materials;
        this.actors = options.actors;
        this.activities = options.activities;
        this.activityGroups = options.activityGroups;
        this.filter = options.filter;
        this.caseStudy = options.caseStudy;
        this.keyflowId = options.keyflowId;
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
        var _this = this,
            html = document.getElementById(this.template).innerHTML
            template = _.template(html);
        this.el.innerHTML = template();
        this.renderSankeyMap();
        var popovers = this.el.querySelectorAll('[data-toggle="popover"]');
        $(popovers).popover({ trigger: "focus" });
    },
    // render the empty sankey map
    renderSankeyMap: function(){
        this.flowMapView = new FlowMapView({
            el: this.el.querySelector('#flow-map'),
            caseStudy: this.caseStudy,
            keyflowId: this.keyflowId,
            materials: this.materials,
            displayWarnings: this.displayWarnings
        });
    },

    // returns parameters for filtered post-fetching based on assigned filter
    getFlowFilterParams: function(){
        var filter = this.filter,
            filterParams = {};

        if(!filter) return filterParams;

        var flowType = filter.get('flow_type') || 'both',
            nodeLevel = filter.get('filter_level') || 'activitygroup',
            direction = filter.get('direction') || 'both';
        flowType = flowType.toLowerCase();
        nodeLevel = nodeLevel.toLowerCase();
        direction = direction.toLowerCase();

        if (flowType != 'both') {
            filterParams.waste = (flowType == 'waste') ? true : false;
        }

        // material options for both stocks and flows
        filterParams.materials = {
            aggregate: filter.get('aggregate_materials')
        }
        var material = filter.get('material'),
            materialIds = [];
        // material -> filter/aggregate by this material and its direct children
        if (material != null) {
            var childMaterials = this.materials.filterBy({ parent: material });
            materialIds = childMaterials.pluck('id');
            // the selected material should be included as well
            filterParams.materials.unaltered = [material];
        }
        // take top level materials to filter, if no material filter
        else {
            var materials = this.materials.filterBy({ parent: null });
            materialIds = materials.pluck('id');
        }
        filterParams.materials.ids = materialIds;

        // if the collections are filtered build matching query params for the flows
        var flowFilterParams = Object.assign({}, filterParams),
            stockFilterParams = Object.assign({}, filterParams);

        var nodeIds = filter.get('node_ids');
        if (nodeIds) nodeIds = nodeIds.split(',');

        var levelFilterMidSec = (nodeLevel == 'activitygroup') ? 'activity__activitygroup__':
            (nodeLevel == 'activity') ? 'activity__': '';

        var flowFilters = flowFilterParams['filters'] = [],
            stockFilters = stockFilterParams['filters'] = [];

        // filter origins/destinations by ids
        if (nodeIds && nodeIds.length > 0){
            var origin_id_filter = {
                    'function': 'origin__'+ levelFilterMidSec + 'id__in',
                    values: nodeIds
                },
                destination_id_filter = {
                    'function': 'destination__'+ levelFilterMidSec + 'id__in',
                    values: nodeIds
                };
            var id_filter = {
                link: 'or',
                functions: []
            }
            if (direction == 'to'){
                id_filter['functions'].push(destination_id_filter);
            }
            else if (direction == 'from') {
                id_filter['functions'].push(origin_id_filter);
            }
            else if (direction == 'both') {
                id_filter['functions'].push(origin_id_filter);
                id_filter['functions'].push(destination_id_filter);
            }
            flowFilters.push(id_filter);
            stockFilters.push({ functions: [origin_id_filter] });
        }

        var areas = filter.get('areas');

        // filter origins/destinations by areas
        if (areas && areas.length > 0){
            var area_filter = {
                link: 'or',
                functions: []
            }
            var origin_area_filter = {
                'function': 'origin__areas',
                values: areas
            }
            var destination_area_filter = {
                'function': 'destination__areas',
                values: areas
            }
            if (direction == 'to'){
                area_filter['functions'].push(destination_area_filter);
            }
            else if (direction == 'from'){
                area_filter['functions'].push(origin_area_filter);
            }
            else if (direction == 'both') {
                area_filter['functions'].push(origin_area_filter);
                area_filter['functions'].push(destination_area_filter);
            }
            flowFilters.push(area_filter);
            stockFilters.push({ functions: [origin_area_filter] });
        }
        return [flowFilterParams, stockFilterParams];
    },

    draw: function(displayLevel){
        if (this.flowMapView != null) this.flowMapView.clear();
        if (this.flowSankeyView != null) this.flowSankeyView.close();
        var displayLevel = displayLevel || 'activitygroup';

        var el = this.el.querySelector('.sankey-wrapper'),
            _this = this;

        // pass all known nodes to sankey (not only the filtered ones) to avoid
        // fetching missing nodes
        var collection = (displayLevel == 'actor') ? this.actors:
            (displayLevel == 'activity') ? this.activities:
            this.activityGroups;
        var filterParams = this.getFlowFilterParams(),
            flowFilterParams = filterParams[0],
            stockFilterParams = filterParams[1];

        flowFilterParams['aggregation_level'] = {
            origin: displayLevel,
            destination: displayLevel
        };
        stockFilterParams['aggregation_level'] = displayLevel;

        var flows = new GDSECollection([], {
            apiTag: 'actorToActor',
            apiIds: [ this.caseStudy.id, this.keyflowId]
        });
        var stocks = new GDSECollection([], {
            apiTag: 'actorStock',
            apiIds: [ this.caseStudy.id, this.keyflowId]
        });
        this.loader.activate();
        var promises = [
            flows.postfetch({body: flowFilterParams})
        ]
        promises.push(stocks.postfetch({body: stockFilterParams}));

        Promise.all(promises).then(function(){
            utils.complementFlowData(flows, collection, collection,
                function(origins, destinations){
                    _this.colorColl(origins);
                    _this.colorColl(destinations);
                    _this.loader.deactivate();
                    _this.flowSankeyView = new FlowSankeyView({
                        el: el,
                        width:  el.clientWidth - 10,
                        origins: origins,
                        destinations: destinations,
                        flows: flows,
                        stocks: stocks,
                        materials: _this.materials,
                        flowFilterParams: flowFilterParams,
                        stockFilterParams: stockFilterParams,
                        hideUnconnected: true,
                        height: 600
                        //originLevel: displayLevel,
                        //destinationLevel: displayLevel
                    })
                    el.addEventListener('linkSelected', _this.linkSelected);
                    el.addEventListener('linkDeselected', _this.linkDeselected);
                    el.addEventListener('allDeselected', _this.deselectAll);
                }
            )
        });

    },

    colorColl: function(collection){
        collection.forEach(function(model){
            var color = utils.colorByName(model.get('name'));
            model.color = color;
        })
    },

    addMapNodes: function(origins, destinations, flows){
        console.log(origins)
        console.log(destinations)
        console.log(flows)
        this.flowMapView.addNodes(destinations);
        this.flowMapView.addNodes(origins);
        this.flowMapView.addFlows(flows);
        //this.flowMapView.rerender(true);
    },

    //
    addGroupedActors: function(origin, destination, flow){

        // put filter params defined by user in filter section into body
        var bodyParams = this.getFlowFilterParams()[0],
            filterSuffix = 'activity';

        // there might be multiple flows in between the same actors,
        // force to aggregate them to one flow
        bodyParams['aggregation_level'] = {origin:"actor",destination:"actor"}

        // put filtering by clicked flow origin/destination into query params
        if (data.flow.get('origin_level') === 'activitygroup')
            filterSuffix += '__activitygroup';
        var queryParams = {};
        queryParams['origin__' + filterSuffix] = origin.id;
        queryParams['destination__' + filterSuffix] = destination.id;

        var flows = new GDSECollection([], {
            apiTag: 'actorToActor',
            apiIds: [_this.caseStudy.id, _this.keyflowId]
        });
        var promise = new Promise(function(resolve, reject){
            flows.postfetch({
                body: bodyParams,
                data: queryParams,
                success: function(){
                    var originIds = [],
                        destinationIds = [];
                    flows.forEach(function(flow){
                        // remember which flow the sub flows belong to (used in deselection)
                        flow.parent = flow.id;
                        originIds.push(flow.get('origin'));
                        destinationIds.push(flow.get('destination'));
                    })
                    var origins = _this.actors.filterBy({id: originIds}),
                        destinations = _this.actors.filterBy({id: destinationIds});
                    utils.complementFlowData(flows, origins, destinations,
                        function(origins, destinations){
                            // assign colors and groups
                            origins.forEach(function(node){
                                node.color = origin.color;
                                node.group = {
                                    color: origin.color,
                                    name: origin.get('name'),
                                    id: origin.id
                                }
                            })
                            destinations.forEach(function(node){
                                node.color = destination.color;
                                node.group = {
                                    color: destination.color,
                                    name: destination.get('name'),
                                    id: destination.id
                                }
                            })
                            _this.addMapNodes(origins.models, destinations.models, flows.models);
                            promise.resolve();
                        }
                    )
                },
                error: promise.reject
            })
        })
    },

    linkSelected: function(e){
        // only actors atm
        var data = e.detail,
            _this = this;
        // display level actor
        if (data.flow.get('origin_level') === 'actor'){
            this.addMapNodes(data.origin, data.destination, data.flow);
            this.flowMapView.rerender(true);
        }
        // display level activity or group
        else {
            this.loader.activate();
            this.addGroupedActors(data.origin, data.destination, data.flow).then(function(){
                _this.loader.deactivate();
                _this.flowMapView.rerender(true);
            })
        }
    },

    linkDeselected: function(e){
        // only actors atm
        var data = e.detail,
            flows = [],
            nodes = [];
        if (data.flow.get('origin_level') === 'actor') {
            nodes = [data.origin, data.destination];
            flows = data.flow;
        }
        else {
            var mapNodes = this.flowMapView.getNodes(),
                mapFlows = this.flowMapView.getFlows(),
                origId = data.flow.get('origin'),
                destId = data.flow.get('destination');
            mapFlows.forEach(function(mapFlow){
                if (mapFlow.parent === data.flow.id){
                    flows.push(mapFlow);
                }
            })
            mapNodes.forEach(function(mapNode){
                var level = data.flow.get('origin_level');
                if ([origId, destId].includes(mapNode.get(level))){
                    nodes.push(mapNode);
                }
            })
        };
        this.flowMapView.removeFlows(flows);
        this.flowMapView.removeNodes(nodes, true);
        this.flowMapView.rerender();
    },

    selectAll: function(){
        this.flowMapView.clear();

    },

    deselectAll: function(){
        this.flowMapView.clear();
        this.flowMapView.rerender();
    }

});
return FlowsView;
}
);

