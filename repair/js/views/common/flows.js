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
        this.nodeLevel = nodeLevel.toLowerCase();
        direction = direction.toLowerCase();

        // material options for stocks and flows
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

        var nodeIds = filter.get('node_ids');
        if (nodeIds) nodeIds = nodeIds.split(',');

        var levelFilterMidSec = (this.nodeLevel == 'activitygroup') ? 'activity__activitygroup__':
            (this.nodeLevel == 'activity') ? 'activity__': '';

        var flowFilters = filterParams['filters'] = [];

        if (flowType != 'both') {
            var is_waste = (flowType == 'waste') ? true : false;
            flowFilters.push({functions: [{'waste': is_waste}]})
        }

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
        }
        return filterParams;
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
        var filterParams = this.getFlowFilterParams();

        filterParams['aggregation_level'] = {
            origin: displayLevel,
            destination: displayLevel
        };

        var flows = new GDSECollection([], {
            apiTag: 'flows',
            apiIds: [ this.caseStudy.id, this.keyflowId]
        });
        this.loader.activate();

        flows.postfetch({
            body: filterParams,
            success: function(response){
                var idx = 0;
                flows.forEach(function(flow){
                    var origin = flow.get('origin'),
                        destination = flow.get('destination');
                    // api aggregates flows and doesn't return an id
                    // generate an internal one to assign interactions
                    flow.id = idx;
                    idx++;
                    origin.color = utils.colorByName(origin.name);
                    if (!flow.get('stock'))
                        destination.color = utils.colorByName(destination.name)
                })
                _this.loader.deactivate();
                _this.flowSankeyView = new FlowSankeyView({
                    el: el,
                    width:  el.clientWidth - 10,
                    flows: flows,
                    hideUnconnected: true,
                    height: 600,
                    originLevel: displayLevel,
                    destinationLevel: displayLevel
                })
                el.addEventListener('linkSelected', _this.linkSelected);
                el.addEventListener('linkDeselected', _this.linkDeselected);
                el.addEventListener('allDeselected', _this.deselectAll);
            },
            error: function(){
                _this.loader.deactivate();
                _this.onError;
            }
        })
    },

    //
    addGroupedActors: function(flow){
        // put filter params defined by user in filter section into body
        var bodyParams = this.getFlowFilterParams(),
            filterSuffix = 'activity',
            _this = this;
        // there might be multiple flows in between the same actors,
        // force to aggregate them to one flow
        bodyParams['aggregation_level'] = { origin:"actor", destination:"actor" }

        // put filtering by clicked flow origin/destination into query params
        if (this.nodeLevel === 'activitygroup')
            filterSuffix += '__activitygroup';
        var queryParams = {};
        queryParams['origin__' + filterSuffix] = flow.get('origin').id;
        queryParams['destination__' + filterSuffix] = flow.get('destination').id;
        queryParams['waste'] = (flow.get('waste')) ? 'True': 'False';

        var flows = new GDSECollection([], {
            apiTag: 'flows',
            apiIds: [this.caseStudy.id, this.keyflowId]
        });
        var promise = new Promise(function(resolve, reject){
            flows.postfetch({
                body: bodyParams,
                data: queryParams,
                success: function(){
                    var originIds = [],
                        destinationIds = [];
                    flows.forEach(function(f){
                        // remember which flow the sub flows belong to (used in deselection)
                        f.parent = flow.id;
                        _this.flowMapView.addFlows(f)
                    })
                    resolve();
                },
                error: reject
            })
        })
        return promise;
    },

    linkSelected: function(e){
        // only actors atm
        var data = e.detail,
            _this = this;

        if (!Array.isArray(data)) data = [data];
        var promises = [];
        this.loader.activate();
        data.forEach(function(d){
            if (!d.get('destination')) return;
            // display level actor
            if (_this.nodeLevel === 'actor'){
                _this.flowMapView.addFlows(d);
            }
            // display level activity or group
            else {
                promises.push(_this.addGroupedActors(d));
            }
        })
        function render(){
            _this.flowMapView.rerender(true);
            _this.loader.deactivate();
        }
        if (promises.length > 0){
            Promise.all(promises).then(render)
        }
        else{
            render();
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

    deselectAll: function(){
        this.flowMapView.clear();
        this.flowMapView.rerender();
    }

});
return FlowsView;
}
);

