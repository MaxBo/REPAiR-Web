define(['views/baseview', 'underscore', 'views/flowsankeymap',
        'collections/gdsecollection', 'views/flowsankey',
        'utils/utils', 'visualizations/map', 'openlayers', 'bootstrap-select'],

function(BaseView, _, FlowMapView, GDSECollection, FlowSankeyView, utils, Map, ol){
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
    * render view to show keyflows in casestudy
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
        _.bindAll(this, 'prepareAreas');
        _.bindAll(this, 'linkSelected');
        _.bindAll(this, 'linkDeselected');

        this.template = options.template;
        this.caseStudy = options.caseStudy;
        this.keyflowId = options.keyflowId;
        this.materials = new GDSECollection([], {
            apiTag: 'materials',
            apiIds: [this.caseStudy.id, this.keyflowId ]
        });
        this.activities = new GDSECollection([], {
            apiTag: 'activities',
            apiIds: [this.caseStudy.id, this.keyflowId ],
            comparator: 'name'
        });
        this.activityGroups = new GDSECollection([], {
            apiTag: 'activitygroups',
            apiIds: [this.caseStudy.id, this.keyflowId ],
            comparator: 'name'
        });
        this.actors = new GDSECollection([], {
            apiTag: 'actors',
            apiIds: [this.caseStudy.id, this.keyflowId],
            comparator: 'name'
        })
        this.areaLevels = new GDSECollection([], {
            apiTag: 'arealevels',
            apiIds: [this.caseStudy.id],
            comparator: 'level'
        });
        this.areas = {};

        this.loader.activate();
        var promises = [
            this.activities.fetch(),
            this.activityGroups.fetch(),
            this.materials.fetch(),
            this.areaLevels.fetch()
        ]
        Promise.all(promises).then(function(){
            _this.activities.sort();
            _this.activityGroups.sort();
            _this.loader.deactivate();
            _this.render();
        })

    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'click #apply-filters': 'renderSankey',
        'click #area-select-button': 'showAreaSelection',
        'change select[name="area-level-select"]': 'changeAreaLevel',
        'change select[name="node-level-select"]': 'resetNodeSelects',
        'click .area-filter.modal .confirm': 'confirmAreaSelection'
    },

    /*
    * render the view
    */
    render: function(){
        var _this = this,
            html = document.getElementById(this.template).innerHTML
            template = _.template(html);
        this.el.innerHTML = template();

        var popovers = this.el.querySelectorAll('[data-toggle="popover"]');
        $(popovers).popover({ trigger: "focus" });

        this.areaModal = this.el.querySelector('.area-filter.modal');
        html = document.getElementById('area-select-modal-template').innerHTML;
        template = _.template(html);
        this.areaModal.innerHTML = template({ levels: this.areaLevels });
        this.areaMap = new Map({
            el: this.areaModal.querySelector('.map'),
        });
        this.areaLevelSelect = this.el.querySelector('select[name="area-level-select"]');
        this.areaMap.addLayer(
            'areas',
            {
                stroke: 'rgb(100, 150, 250)',
                fill: 'rgba(100, 150, 250, 0.5)',
                select: {
                    selectable: true,
                    stroke: 'rgb(230, 230, 0)',
                    fill: 'rgba(230, 230, 0, 0.5)',
                    onChange: function(areaFeats){
                        var modalSelDiv = _this.el.querySelector('.selections'),
                            levelId = _this.areaLevelSelect.value
                            labels = [],
                            areas = _this.areas[levelId];
                        _this.selectedAreas = [];
                        areaFeats.forEach(function(areaFeat){
                            labels.push(areaFeat.label);
                            _this.selectedAreas.push(areas.get(areaFeat.id))
                        });
                        modalSelDiv.innerHTML = labels.join(', ');
                    }
                }
            });
        this.changeAreaLevel();

        // event triggered when modal dialog is ready -> trigger rerender to match size
        $(this.areaModal).on('shown.bs.modal', function () {
            _this.areaMap.map.updateSize();
        });
        this.displayLevelSelect = this.el.querySelector('select[name="display-level-select"]');
        this.nodeLevelSelect = this.el.querySelector('select[name="node-level-select"]');
        this.groupSelect = this.el.querySelector('select[name="group"]'),
        this.activitySelect = this.el.querySelector('select[name="activity"]'),
        this.actorSelect = this.el.querySelector('select[name="actor"]');
        $(this.groupSelect).selectpicker();
        $(this.activitySelect).selectpicker();
        $(this.actorSelect).selectpicker();
        this.resetNodeSelects();
        this.renderMatFilter();
        this.addEventListeners();
        // render with preset selects (group level, all materials etc.)
        this.renderSankey();
        this.renderSankeyMap();
    },

    resetNodeSelects: function(){

        var level = this.nodeLevelSelect.value,
            hide = [],
            selects = [this.actorSelect, this.groupSelect, this.activitySelect],
            areaSelectWrapper = this.el.querySelector('.area-select-wrapper');

        // show the grandparents
        selects.forEach(function(sel){
            sel.parentElement.parentElement.style.display = 'block';
            sel.selectedIndex = 0;
            sel.style.height ='100%'; // resets size, in case it was expanded
        })
        areaSelectWrapper.parentElement.parentElement.style.display = 'block';

        if (level == 'activity'){
            hide = [this.actorSelect, areaSelectWrapper];
        }
        if (level == 'activitygroup'){
            hide = [this.actorSelect, this.activitySelect, areaSelectWrapper];
        }

        // hide the grandparents
        hide.forEach(function(s){
            s.parentElement.parentElement.style.display = 'none';
        })
        this.renderNodeSelectOptions(this.groupSelect, this.activityGroups);
        if(level != 'activitygroup')
            this.renderNodeSelectOptions(this.activitySelect, this.activities);
        if(level == 'actor')
            this.renderNodeSelectOptions(this.actorSelect);
    },

    changeAreaLevel: function(){
        var levelId = this.areaLevelSelect.value;
        this.el.querySelector('.selections').innerHTML = this.el.querySelector('#area-selections').innerHTML= '';
        this.prepareAreas(levelId);
    },

    prepareAreas: function(levelId){
        var _this = this;
        this.areaMap.clearLayer('areas');
        var areas = this.areas[levelId];
        if (areas){
            this.drawAreas(areas)
        }
        else {
            areas = new GDSECollection([], {
                apiTag: 'areas',
                apiIds: [ this.caseStudy.id, levelId ]
            });
            this.areas[levelId] = areas;
            var loader = new utils.Loader(this.areaModal, {disable: true});
            loader.activate();
            areas.fetch({
                success: function(){
                    loader.deactivate();
                    _this.drawAreas(areas)
                },
                error: function(res) {
                    loader.deactivate();
                    _this.onError(res);
                }
            });
        }
    },

    drawAreas: function(areas){
        var _this = this;
        areas.forEach(function(area){
            var coords = area.get('geometry').coordinates,
                name = area.get('name');
            _this.areaMap.addPolygon(coords, {
                projection: 'EPSG:4326', layername: 'areas',
                type: 'MultiPolygon', tooltip: name,
                label: name, id: area.id
            });
        })
        this.areaMap.centerOnLayer('areas');
    },

    showAreaSelection: function(){
        $(this.areaModal).modal('show');
    },

    confirmAreaSelection: function(){
        // lazy way to show the selected areas, just take it from the modal
        var modalSelDiv = this.el.querySelector('.selections'),
            selDiv = this.el.querySelector('#area-selections');
        selDiv.innerHTML = modalSelDiv.innerHTML;
        this.filterActors();
    },

    filterActors: function(){
        var _this = this,
            geoJSONText,
            queryParams = {
                included: 'True',
                fields: ['id', 'name'].join()
            };

        var actors = this.actors,
            activity = this.activitySelect.value,
            group = this.groupSelect.value;

        // take selected activities for querying specific actors
        if(activity >= 0){
            var activities = this.getSelectedNodes(this.activitySelect);
            queryParams['activity__id__in'] = [activities].join(',');
        }
        // or take selected groups if activity is set to 'All'
        else if (group >= 0) {
            var groups = this.getSelectedNodes(this.groupSelect);
            queryParams['activity__activitygroup__id__in'] = [groups].join(',');
        }
        // if there are areas selected merge them to single multipolygon
        // and serialize that to geoJSON
        if (this.selectedAreas && this.selectedAreas.length > 0) {
            var multiPolygon = new ol.geom.MultiPolygon();
            this.selectedAreas.forEach(function(area){
                var geom = area.get('geometry'),
                    coordinates = geom.coordinates;
                if (geom.type == 'MultiPolygon'){
                    var multi = new ol.geom.MultiPolygon(coordinates),
                        polys = multi.getPolygons();
                    polys.forEach( function(poly) {multiPolygon.appendPolygon(poly);} )
                }
                else{
                    var poly = new ol.geom.Polygon(coordinates);
                    multiPolygon.appendPolygon(poly);
                }
            })
            var geoJSON = new ol.format.GeoJSON(),
            geoJSONText = geoJSON.writeGeometry(multiPolygon);
        }
       // area: geoJSONText,
        this.loader.activate({offsetX: '20%'});
        this.actors.postfetch({
            data: queryParams,
            body: { area: geoJSONText },
            success: function(response){
                _this.loader.deactivate();
                _this.actors.sort();
                _this.renderNodeSelectOptions(_this.actorSelect, _this.actors);
                _this.actorSelect.value = -1;
            },
            reset: true
        })
    },

    // returns parameters for filtered post-fetching of flows depending on
    // selections the user made in Filter section (display level excluded)
    getFlowFilterParams: function(){

        var filterParams = {},
            waste = this.el.querySelector('select[name="waste"]').value,
            nodeLevel = this.nodeLevelSelect.value,
            direction = this.el.querySelector('input[name="direction"]:checked').value;
        if (waste) filterParams.waste = waste;

        // material options for both stocks and flows
        var aggregateMaterials = this.el.querySelector('input[name="aggregateMaterials"]').checked;
        filterParams.materials = {
            aggregate: aggregateMaterials
        }
        var material = this.selectedMaterial,
            materialIds = [];

        // material is selected -> filter/aggregate by this material and its direct children
        if (material) {
            var childMaterials = this.materials.filterBy({ parent: material.id });
            materialIds = childMaterials.pluck('id');
            // the selected material should be included as well
            filterParams.materials.unaltered = [material.id];
        }
        // take top level materials to aggregate to
        else {
            var materials = this.materials.filterBy({ parent: null });
            materialIds = materials.pluck('id');
        }
        filterParams.materials.ids = materialIds;

        // if the collections are filtered build matching query params for the flows
        var flowFilterParams = Object.assign({}, filterParams);
        var stockFilterParams = Object.assign({}, filterParams);
        var nodeIds = [];

        var nodeIds = this.getSelectedNodes();
        nodeIds.forEach(function(id){
            nodeIds.push(id);
        })

        var levelFilterMidSec = (nodeLevel == 'activitygroup') ? 'activity__activitygroup__':
            (nodeLevel == 'activity') ? 'activity__': '';

        var flowFilters = flowFilterParams['filters'] = [],
            stockFilters = stockFilterParams['filters'] = [],
            origin_filter = {
                'function': 'origin__'+ levelFilterMidSec + 'id__in',
                values: nodeIds
            },
            destination_filter = {
                'function': 'destination__'+ levelFilterMidSec + 'id__in',
                values: nodeIds
            };

        if (nodeIds.length>0){
            if (direction == 'to'){
                flowFilters.push(destination_filter);
            }
            if (direction == 'from') {
                flowFilters.push(origin_filter);
            }
            if (direction == 'both') {
                flowFilters.push(origin_filter);
                flowFilters.push(destination_filter);
            }
            stockFilters.push(origin_filter);
        }
        return [flowFilterParams, stockFilterParams];
    },

    renderSankey: function(){
        if (this.flowMapView != null) this.flowMapView.clear();
        if (this.flowsView != null) this.flowsView.close();
        var el = this.el.querySelector('.sankey-wrapper'),
            displayLevel = this.displayLevelSelect.value,
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
                    _this.loader.deactivate();
                    _this.flowsView = new FlowSankeyView({
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
                }
            )
        });

    },

    linkSelected: function(e){
        // only actors atm
        var data = e.detail,
            _this = this;
        function render(origins, destinations, flows){
            _this.flowMapView.addNodes(destinations);
            _this.flowMapView.addNodes(origins);
            _this.flowMapView.addFlows(flows);
            _this.flowMapView.rerender();
        }

        // fetch actors and the flows in between them when group or activity was selected,
        // render after fetching
        function fetchRenderData(origin, destination, queryParams, bodyParams) {
            var promises = [],
                actorIds = [],
                nodes = [];

            _this.loader.activate();
            var flows = new GDSECollection([], {
                apiTag: 'actorToActor',
                apiIds: [_this.caseStudy.id, _this.keyflowId]
            });
            actorIds = actorIds.join(',');
            flows.postfetch({
                body: bodyParams,
                data: queryParams,
                success: function(){
                    var originIds = [],
                        destinationIds = [];
                    flows.forEach(function(flow){
                        // remember which flow the sub flows belong to (used in deselection)
                        flow.parent = data.flow.id;
                        originIds.push(flow.get('origin'));
                        destinationIds.push(flow.get('destination'));
                    })
                    var origins = _this.actors.filterBy({id: originIds}),
                        destinations = _this.actors.filterBy({id: destinationIds});
                    utils.complementFlowData(flows, origins, destinations,
                        function(origins, destinations){
                            origins.forEach(function(node){ node.color = origin.color; })
                            destinations.forEach(function(node){ node.color = destination.color; })
                            _this.loader.deactivate();
                            render(origins.models, destinations.models, flows.models);
                        }
                    )
                }
            })
        }
        // display level actor
        if (data.flow.get('origin_level') === 'actor'){
            render(data.origin, data.destination, data.flow);
        }
        // display level activity or group
        else {
            // put filter params defined by user in filter section into body
            var bodyParams = this.getFlowFilterParams()[0],
                filterSuffix = 'activity';

            // put filtering by clicked flow origin/destination into query params
            if (data.flow.get('origin_level') === 'activitygroup')
                filterSuffix += '__activitygroup';
            var queryParams = {};
            queryParams['origin__' + filterSuffix] = data.origin.id;
            queryParams['destination__' + filterSuffix] = data.destination.id;

            // fetch flows with filter params
            fetchRenderData(data.origin, data.destination, queryParams, bodyParams);
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

    renderSankeyMap: function(){
        this.flowMapView = new FlowMapView({
            el: this.el.querySelector('#flow-map'),
            caseStudyId: this.caseStudy.id,
            keyflowId: this.keyflowId,
            materials: this.materials
        });

    },

    // filter section: get the selected nodes of selected level
    getSelectedNodes: function(nodeSelect){
        if (!nodeSelect){
            var level = this.nodeLevelSelect.value,
                nodeSelect = (level == 'actor') ? this.actorSelect:
                             (level == 'activity') ? this.activitySelect:
                             this.groupSelect;
        }
        function getValues(selectOptions){
            var values = [];
            for (var i = 0; i < selectOptions.length; i++) {
                var option = selectOptions[i];
                if (option.dataset.divider) continue;
                var id = option.value;
                // ignore 'All' in multi select
                if (id >= 0)
                    values.push(id);
            }
            return values;
        }
        // value will always return the value of the top selected option
        // so if it is > -1 "All" is not selected
        if (nodeSelect.value >= 0){
            selected = nodeSelect.selectedOptions;
            return getValues(selected);
        }
        // "All" is selected -> return values of all options (except "All")
        else {
            // exception: we don't render the actor nodes into the select, if there are too many
            // this.actors contains the filtered actors, return their ids instead
            if (level == 'actor'){
                return this.actors.pluck('id');
            }
            // for group and activity the selected nodes represent the filtering
            return getValues(nodeSelect.options)
        }
    },

    renderNodeSelectOptions: function(select, collection){
        utils.clearSelect(select);
        var defOption = document.createElement('option');
        defOption.value = -1;
        defOption.text = gettext('All');
        if (collection) defOption.text += ' (' + collection.length + ')';
        select.appendChild(defOption);
        var option = document.createElement('option');
        option.dataset.divider = 'true';
        select.appendChild(option);
        if (collection && collection.length < 2000){
            collection.forEach(function(model){
                var option = document.createElement('option');
                option.value = model.id;
                option.text = model.get('name');
                select.appendChild(option);
            })
            select.disabled = false;
        }
        else {
            defOption.text += ' - ' + gettext('too many to display');
            select.disabled = true;
        }
        select.selectedIndex = 0;
        $(select).selectpicker('refresh');
    },


    addEventListeners: function(){
        var _this = this;

        function multiCheck(evt, clickedIndex, checked){
            var select = evt.target;
            if(checked){
                // 'All' clicked -> deselect other options
                if (clickedIndex == 0){
                   $(select).selectpicker('deselectAll');
                    select.value = -1;
                }
                // other option clicked -> deselect 'All'
                else {
                    select.options[0].selected = false;
                }
                $(select).selectpicker('refresh');
            }
        }

        $(this.groupSelect).on('changed.bs.select', function(evt, index, val){
            multiCheck(evt, index, val);
            var level = _this.nodeLevelSelect.value;

            var filteredActivities = _this.activities;

            // filter activities by group selection if sth different than 'All' is selected
            if (_this.groupSelect.value > 0){
                var groupIds = _this.getSelectedNodes(_this.groupSelect);
                filteredActivities = _this.activities.filterBy({'activitygroup': groupIds});
            }

            _this.renderNodeSelectOptions(_this.activitySelect, filteredActivities);
            // nodelevel actor is selected -> filter actors
            if (level == 'actor')
                _this.filterActors();
        })

        $(this.activitySelect).on('changed.bs.select', function(evt, index, val){
            multiCheck(evt, index, val);
            // nodelevel actor is selected -> filter actors
            if (_this.nodeLevelSelect.value == 'actor')
                _this.filterActors();
        })

        $(this.actorSelect).on('changed.bs.select', multiCheck);
    },

    renderMatFilter: function(){
        var _this = this;
        // select material
        var matSelect = document.createElement('div');
        matSelect.classList.add('materialSelect');
        this.hierarchicalSelect(this.materials, matSelect, {
            onSelect: function(model){
                 _this.selectedMaterial = model;
            },
            defaultOption: gettext('All materials')
        });
        this.el.querySelector('#material-filter').appendChild(matSelect);
    },

});
return FlowsView;
}
);
