define(['views/common/baseview', 'underscore', 'views/common/flowsankeymap',
        'collections/gdsecollection', 'models/gdsemodel',
        'views/common/flowsankey', 'utils/utils', 'backbone'],

function(BaseView, _, FlowMapView, GDSECollection, GDSEModel,
         FlowSankeyView, utils, Backbone){
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
        this.strategy = options.strategy;
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
        'change select[name="modification-select"]': 'redraw'
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

        this.sankeyWrapper = this.el.querySelector('.sankey-wrapper');
        this.sankeyWrapper.addEventListener('linkSelected', this.linkSelected);
        this.sankeyWrapper.addEventListener('linkDeselected', this.linkDeselected);
        this.sankeyWrapper.addEventListener('allDeselected', this.deselectAll);

        var deltaEl = this.el.querySelector('div[name="modifications"]');
        this.modDisplaySelect = this.el.querySelector('select[name="modification-select"]');
        if(this.strategy){
            deltaEl.style.display = 'block';
        }
    },
    // render the empty sankey map
    renderSankeyMap: function(){
        this.flowMapView = new FlowMapView({
            el: this.el.querySelector('#flow-map'),
            caseStudy: this.caseStudy,
            keyflowId: this.keyflowId,
            materials: this.materials,
            displayWarnings: this.displayWarnings,
            anonymize: this.filter.get('anonymize')
        });
    },

    // returns parameters for filtered post-fetching based on assigned filter
    getFlowFilterParams: function(){
        var filter = this.filter,
            filterParams = {};

        if(!filter) return filterParams;

        var flowType = filter.get('flow_type') || 'both',
            hazardous = filter.get('hazardous').toLowerCase(),
            avoidable = filter.get('avoidable').toLowerCase(),
            nodeLevel = filter.get('filter_level') || 'activitygroup',
            direction = filter.get('direction') || 'both';

        nodeLevel = nodeLevel.toLowerCase();
        flowType = flowType.toLowerCase();
        direction = direction.toLowerCase();

        // material options for stocks and flows
        filterParams.materials = {
            aggregate: filter.get('aggregate_materials')
        }

        var material = filter.get('material');
        // material -> filter/aggregate by this material and its direct children
        if (material != null) {
            var childMaterials = this.materials.filterBy({ parent: material }),
                materialIds = childMaterials.pluck('id');
            // the selected material should be included as well
            filterParams.materials.unaltered = [material];
            filterParams.materials.ids = materialIds;
        }
        var nodeIds = filter.get('node_ids');
        if (nodeIds) nodeIds = nodeIds.split(',');

        var levelFilterMidSec = (nodeLevel == 'activitygroup') ? 'activity__activitygroup__':
            (nodeLevel == 'activity') ? 'activity__': '';

        var flowFilters = filterParams['filters'] = [];

        var typeFilterFunctions = {};
        if (flowType != 'both') {
            var is_waste = (flowType == 'waste') ? true : false;
            typeFilterFunctions['waste'] = is_waste;
        }
        if (hazardous != 'both') {
            var is_hazardous = (hazardous == 'yes') ? true : false;
            typeFilterFunctions['hazardous'] = is_hazardous;
        }
        if (avoidable != 'both') {
            var is_avoidable = (avoidable == 'yes') ? true : false;
            typeFilterFunctions['avoidable'] = is_avoidable
        }
        var processIds = filter.get('process_ids');
        if (processIds) {
            typeFilterFunctions['process_id__in'] = processIds.split(',');
        }

        if (Object.keys(typeFilterFunctions).length > 0) {
            typeFilterFunctions['link'] = 'and';
            flowFilters.push(typeFilterFunctions);
        }

        // filter origins/destinations by ids
        if (nodeIds && nodeIds.length > 0) {
            var id_filter = { link: 'or' };
            if (direction == 'to' || direction == 'both'){
                id_filter['destination__'+ levelFilterMidSec + 'id__in'] = nodeIds;
            }
            if (direction == 'from' || direction == 'both') {
                id_filter['origin__'+ levelFilterMidSec + 'id__in'] = nodeIds;
            }
            flowFilters.push(id_filter);
        }

        var areas = filter.get('areas');

        // filter origins/destinations by areas
        if (areas && areas.length > 0){
            var area_filter = { link: 'or' }
            if (direction == 'to' || direction == 'both'){
                area_filter['destination__areas'] = areas;
            }
            if (direction == 'from' || direction == 'both'){
                area_filter['origin__areas'] = areas;
            }
            flowFilters.push(area_filter);
        }
        return filterParams;
    },

    redraw: function(){
        var showDelta = this.modDisplaySelect.value === 'delta',
            dblCheck = this.el.querySelector('#sankey-dblclick'),
            mapWrapper = this.flowMapView.el.parentElement;
        if (dblCheck) dblCheck.parentElement.style.display = (showDelta) ? 'None': 'block';
        if (showDelta)
            mapWrapper.classList.add('disabled');
        else
            mapWrapper.classList.remove('disabled');
        if (!this.displayLevel) return;
        this.draw(this.displayLevel);
    },

    postprocess: function(flows){
        var idx = 0;
        flows.forEach(function(flow){
            var origin = flow.get('origin'),
                destination = flow.get('destination');
            // api aggregates flows and doesn't return an id
            // generate an internal one to assign interactions
            flow.set('id', idx);
            idx++;

            // remember original amounts to be able to swap amount with delta and back
            flow._amount = flow.get('amount');
            var materials = flow.get('materials');
            flow.get('materials').forEach(function(material){
                material._amount =  material.amount;
            })
            flow.set('materials', materials);

            origin.color = utils.colorByName(origin.name);
            if (!flow.get('stock'))
                destination.color = utils.colorByName(destination.name);
        })
    },

    // fetch flows and calls options.success(flows) on success
    // options.displayLevel
    // options.strategy to fetch strategy flows
    fetchFlows: function(options){
        var filterParams = this.getFlowFilterParams(),
            displayLevel = options.displayLevel || 'activitygroup',
            _this = this;
        filterParams['aggregation_level'] = {
            origin: displayLevel,
            destination: displayLevel
        };

        var flows = new GDSECollection([], {
            apiTag: 'flows',
            apiIds: [ this.caseStudy.id, this.keyflowId]
        });

        this.loader.activate();
        var data = {};
        if (options.strategy)
            data['strategy'] = this.strategy.id;

        flows.postfetch({
            data: data,
            body: filterParams,
            success: function(response){
                _this.postprocess(flows);
                _this.loader.deactivate();
                if (options.success)
                    options.success(flows);
            },
            error: function(error){
                _this.loader.deactivate();
                _this.onError(error);
            }
        })
    },

    calculateDelta: function(statusQuoFlows, strategyFlows){
        var deltaFlows = new Backbone.Collection(null, { model: GDSEModel });

        function find(flow, collection){
            var originId = flow.get('origin').id,
                destination = flow.get('destination'),
                destinationId = (destination) ? destination.id: null,
                waste = flow.get('waste'),
                process_id = flow.get('process_id'),
                hazardous = flow.get('hazardous');
            var found = statusQuoFlows.filter(function(model){
                var sqDest = model.get('destination'),
                    sqDestId = (sqDest) ? sqDest.id: null;
                return ((model.get('origin').id == originId) &&
                        (destinationId == sqDestId) &&
                        (model.get('waste') == waste) &&
                        (model.get('process_id') == process_id) &&
                        (model.get('hazardous') == hazardous));
            });
            return found;
        }

        function mergeMaterials(statusQuoMaterials, strategyMaterials){
            var sfMats = {},
                sqMats = {},
                materials = [];
            if (strategyMaterials)
                strategyMaterials.forEach(function(material){
                    var key = material.material;
                    sfMats[key] = material;
                })
            statusQuoMaterials.forEach(function(material){
                var key = material.material;
                sqMats[key] = material;
            })
            for (let [key, sfMaterial] of Object.entries(sfMats)){
                var sqMaterial = sqMats[key],
                    sfClone = Object.assign({}, sfMaterial);
                // material is in both: delta
                if (sqMaterial)
                    sfClone.amount -= sqMaterial.amount;
                // material only in strategy: keep as is
                materials.push(sfClone);
            }
            for (let [key, sqMaterial] of Object.entries(sqMats)){
                var sfMaterial = sfMats[key];
                // material not in strategy
                if (!sfMaterial){
                    var sqClone = Object.assign({}, sfMaterial);
                    sqClone.amount = -sqClone.amount;
                    materials.push(sqClone);
                }
            }
            return materials;
        }

        function hash(collection){
            var hashed = {};
            collection.forEach(function(model){
                var originId = model.get('origin').id,
                    destination = model.get('destination'),
                    destinationId = (destination) ? destination.id: null,
                    waste = model.get('waste'),
                    processId = model.get('process_id'),
                    hazardous = model.get('hazardous');
                var key = originId + '-' + destinationId + '-' + waste + '-' + processId + '-' + hazardous;
                hashed[key] = model;
            })
            return hashed;
        }

        var sfHashed = hash(strategyFlows);
            sqHashed = hash(statusQuoFlows);

        for (let [key, strategyFlow] of Object.entries(sfHashed)) {
            var statusQuoFlow = sqHashed[key],
                deltaFlow = strategyFlow.clone();

            // strategy flow already existed in status quo
            if (statusQuoFlow){
                var mergedMaterials = mergeMaterials(statusQuoFlow.get('materials'), strategyFlow.get('materials'));
                deltaFlow.set('materials', mergedMaterials);
                deltaFlow.set('amount', strategyFlow.get('amount') - statusQuoFlow.get('amount'));
            }
            // strategy flow is completely new
            else {
                deltaFlow.set('amount', strategyFlow.get('amount'));
            }
            deltaFlows.add(deltaFlow);
        }

        for (let [key, statusQuoFlow] of Object.entries(sqHashed)) {
            var strategyFlow = sfHashed[key];

            // status quo flow does not exist in strategy anymore
            if (!strategyFlow){
                deltaFlow = statusQuoFlow.clone();
                deltaFlow.set('amount', -statusQuoFlow.get('amount'));
                var mergedMaterials = mergeMaterials(statusQuoFlow.get('materials'), null);
                deltaFlow.set('materials', mergedMaterials);
                var materials = statusQuoFlow.get('materials');
                deltaFlows.add(deltaFlow);
            }
        }
        return deltaFlows;
    },

    draw: function(displayLevel){
        this.flowMem = {};
        if (this.flowMapView != null) this.flowMapView.clear();
        if (this.flowSankeyView != null) this.flowSankeyView.close();
        var displayLevel = displayLevel || 'activitygroup';

        this.nodeLevel = displayLevel.toLowerCase();

        var el = this.sankeyWrapper,
            showDelta = this.modDisplaySelect.value === 'delta',
            _this = this;

        function drawSankey(){
            var modDisplay = _this.modDisplaySelect.value,
                flows = (modDisplay == 'statusquo') ? _this.flows : (modDisplay == 'strategy') ? _this.strategyFlows : _this.deltaFlows;
            // override value and color
            flows.forEach(function(flow){
                var amount = flow._amount;
                flow.color = (!showDelta) ? null: (amount > 0) ? '#23FE01': 'red';
                flow.set('amount', amount)
                var materials = flow.get('materials');
                flow.get('materials').forEach(function(material){
                    material.amount = material._amount;
                })
                flow.set('materials', materials);
            });
            _this.flowSankeyView = new FlowSankeyView({
                el: el,
                width:  el.clientWidth - 10,
                flows: flows,
                height: 600,
                originLevel: displayLevel,
                destinationLevel: displayLevel,
                anonymize: _this.filter.get('anonymize'),
                showRelativeComposition: !showDelta,
                forceSignum: showDelta
            })
        }
        // no need to fetch flows if display level didn't change from last time
        if (this.displayLevel != displayLevel) {
            this.fetchFlows({
                displayLevel: displayLevel,
                success: function(flows){
                    _this.flows = flows;
                    if (_this.strategy){
                        _this.fetchFlows({
                            strategy: _this.strategy,
                            displayLevel: displayLevel,
                            success: function(strategyFlows){
                                _this.strategyFlows = strategyFlows;
                                _this.deltaFlows = _this.calculateDelta(_this.flows, strategyFlows);
                                _this.postprocess(_this.deltaFlows);
                                drawSankey();
                            }
                        })
                    } else
                        drawSankey();
                }
            })
        }
        else {
            drawSankey();
        }
        this.displayLevel = displayLevel;
    },

    addGroupedActors: function(flow){
        // put filter params defined by user in filter section into body
        var bodyParams = this.getFlowFilterParams(),
            filterSuffix = 'activity',
            _this = this,
            showDelta = this.modDisplaySelect.value === 'delta';
        // there might be multiple flows in between the same actors,
        // force to aggregate them to one flow
        bodyParams['aggregation_level'] = { origin:"actor", destination:"actor" }

        // put filtering by clicked flow origin/destination into query params
        if (this.nodeLevel === 'activitygroup')
            filterSuffix += '__activitygroup';
        var queryParams = {},
            is_stock = flow.get('stock'),
            process = flow.get('process_id');
        queryParams['origin__' + filterSuffix] = flow.get('origin').id;
        if (!is_stock)
            queryParams['destination__' + filterSuffix] = flow.get('destination').id;
        queryParams['waste'] = (flow.get('waste')) ? 'True': 'False';
        queryParams['stock'] = (is_stock) ? 'True': 'False';
        if (process)
            queryParams['process'] = process;
        else
            queryParams['process__isnull'] = true;

        if (this.strategy && this.modDisplaySelect.value != 'statusquo')
            queryParams['strategy'] = this.strategy.id;

        var origin = flow.get('origin'),
            destination = flow.get('destination'),
            destination_group = null;
            origin_group = {
                color: origin.color,
                name: origin.name,
                id: origin.id
            };
        if (!is_stock)
            destination_group = {
                color: destination.color,
                name: destination.name,
                id: destination.id
            };

        var flows = new GDSECollection([], {
            apiTag: 'flows',
            apiIds: [this.caseStudy.id, this.keyflowId]
        });

        function addFlows(flows){
            // override value and color
            flows.forEach(function(flow){
                var amount = flow._amount;
                flow.color = (!showDelta) ? null: (amount > 0) ? '#23FE01': 'red';
                flow.set('amount', amount)
                var materials = flow.get('materials');
                flow.get('materials').forEach(function(material){
                    material.amount = material._amount;
                })
                flow.set('materials', materials);
            });
            _this.flowMapView.addFlows(flows);
        }

        var promise = new Promise(function(resolve, reject){
            var mem = _this.flowMem[flow.id];
            // flows were not fetched yet
            if (!mem){
                flows.postfetch({
                    body: bodyParams,
                    data: queryParams,
                    success: function(flows){
                        flows.forEach(function(f){
                            // remember which flow the sub flows belong to (used in deselection)
                            f.parent = flow.id;
                            var o = f.get('origin');
                            o.group = origin_group;
                            o.color = origin.color;
                            var d = f.get('destination');
                            if (d) {
                                d.group = destination_group;
                                d.color = destination.color;
                            }
                            // remember original amounts to be able to swap amount with delta and back
                            f._amount = f.get('amount');
                            var materials = f.get('materials');
                            f.get('materials').forEach(function(material){
                                // ToDo: change filter API response
                                // workaround: show statusquo if amount is null
                                if (material.amount == null) material.amount = material.statusquo_amount;
                                material._amount = material.amount;
                            })
                            f.set('materials', materials);
                        })
                        addFlows(flows);
                        _this.flowMem[flow.id] = flows;
                        resolve();
                    },
                    error: reject
                })
            }
            // add already fetched nodes
            else {
                addFlows(mem);
                resolve();
            }
        })
        return promise;
    },

    linkSelected: function(e){
        // only actors atm
        var data = e.detail,
            _this = this,
            showDelta = this.modDisplaySelect.value === 'delta';

        if (showDelta) return;

        if (!Array.isArray(data)) data = [data];
        var promises = [];
        this.loader.activate();
        data.forEach(function(d){

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
        var flow = e.detail,
            flows = [],
            nodes = [];
        if (this.nodeLevel === 'actor') {
            nodes = [data.origin, data.destination];
            flows = flow;
        }
        else {
            var mapFlows = this.flowMapView.getFlows();
            mapFlows.forEach(function(mapFlow){
                if (mapFlow.parent === flow.id){
                    flows.push(mapFlow);
                }
            })
        };
        this.flowMapView.removeFlows(flows);
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

