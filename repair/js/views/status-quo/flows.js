define(['views/baseview', 'underscore', 'visualizations/flowmap',
        'collections/gdsecollection', 'views/flowsankey', 
        'utils/utils', 'visualizations/map', 'openlayers', 'bootstrap-select'],

function(BaseView, _, FlowMap, GDSECollection, FlowSankeyView, utils, Map, ol){
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
        _.bindAll(this, 'refreshSankeyMap');
        _.bindAll(this, 'prepareAreas');

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
        this.areaLevels = new GDSECollection([], { 
            apiTag: 'arealevels',
            apiIds: [this.caseStudy.id],
            comparator: 'level'
        });
        this.areas = {};
        this.filters = {};
        this.filtersTmp = {};
        
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
        'click #apply-filters': 'applyFilters',
        'change #data-view-type-select': 'renderSankey',
        'click #area-select-button': 'showAreaSelection',
        'change select[name="level-select"]': 'changeAreaLevel',
        'click #area-filter-modal .confirm': 'confirmAreaSelection'
    },

    /*
    * render the view
    */
    render: function(){
        var _this = this;
        var html = document.getElementById(this.template).innerHTML
        var template = _.template(html);
        this.el.innerHTML = template({ levels: this.areaLevels });
        
        this.areaModal = document.getElementById('area-filter-modal');
        this.areaMap = new Map({
            divid: 'area-select-map', 
        });
        this.levelSelect = this.el.querySelector('select[name="level-select"]');
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
                        var modalSelDiv = _this.el.querySelector('#modal-area-selections'),
                            levelId = _this.levelSelect.value
                            labels = [],
                            areas = _this.areas[levelId];
                        _this.filtersTmp['areas'] = [];
                        areaFeats.forEach(function(areaFeat){
                            labels.push(areaFeat.label);
                            _this.filtersTmp['areas'].push(areas.get(areaFeat.id))
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
        this.groupSelect = this.el.querySelector('select[name="group"]'),
        this.activitySelect = this.el.querySelector('select[name="activity"]'),
        this.actorSelect = this.el.querySelector('select[name="actor"]');
        $(this.groupSelect).selectpicker();
        $(this.activitySelect).selectpicker();
        $(this.actorSelect).selectpicker();
        this.typeSelect = this.el.querySelector('#data-view-type-select');
        this.renderMatFilter();
        this.renderNodeFilters();
        this.applyFilters();
    },
    
    changeAreaLevel: function(){
        var levelId = this.levelSelect.value;
        this.el.querySelector('#modal-area-selections').innerHTML = this.el.querySelector('#area-selections').innerHTML= '';
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
                    var promises = [];
                    areas.forEach(function(area){
                        promises.push(
                            area.fetch({ error: _this.onError })
                        )
                    });
                    Promise.all(promises).then(function(){
                        loader.deactivate();
                        _this.drawAreas(areas)
                    });
                }, error: function(res) {
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
        this.selectedAreas = this.filtersTmp['areas'];
        // lazy way to show the selected areas, just take it from the modal
        var modalSelDiv = this.el.querySelector('#modal-area-selections'),
            selDiv = this.el.querySelector('#area-selections');
        selDiv.innerHTML = modalSelDiv.innerHTML;
        this.filterActors();
    },
    
    filterActors: function(){
        var _this = this,
            geoJSONText, 
            queryParams = { 
                included: 'True', 
                fields: ['id', 'name', 'description', 'activity', 'activitygroup'].join() 
            };
        
        var activity = this.activitySelect.value,
            group = this.groupSelect.value;
        
        // actually no need to create this new, but easier to handle
        this.actorsTmp = new GDSECollection([], {
            apiTag: 'actors',
            apiIds: [this.caseStudy.id, this.keyflowId],
            comparator: 'name'
        })
        
        if(activity >= 0) queryParams['activity'] = activity;
        else if (group >= 0) queryParams['activity__activitygroup'] = group;
            
        // if there are areas selected merge them to single multipolygon
        // and serialize that to geoJSON
        if (_this.selectedAreas && _this.selectedAreas.length > 0) {
            var multiPolygon = new ol.geom.MultiPolygon();
            _this.selectedAreas.forEach(function(area){ 
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
        this.actorsTmp.postfetch({
            data: queryParams,
            body: { area: geoJSONText },
            success: function(response){
                _this.loader.deactivate();
                _this.actorsTmp.sort();
                _this.renderNodeSelectOptions(_this.actorSelect, _this.actorsTmp);
                _this.actorSelect.value = -1;
            }
        })
        
    },

    refreshSankeyMap: function(){
        if (this.sankeyMap) this.sankeyMap.refresh();
    },
    
    applyFilters: function(){
        this.filters['activities'] = this.filtersTmp['activities'] || this.activities;
        this.filters['groups'] = this.filtersTmp['groups'] || this.activityGroups;
        this.filters['direction'] = this.el.querySelector('input[name="direction"]:checked').value;
        this.filters['waste'] = this.el.querySelector('select[name="waste"]').value;
        this.filters['aggregateMaterials'] = this.el.querySelector('input[name="aggregateMaterials"]').checked;
        this.filters['material'] = this.filtersTmp['material'];
        this.filters['actors'] = this.filtersTmp['actors'] || this.actorsTmp;
        this.actors = this.actorsTmp;
        this.renderSankey();
    },
    
    renderSankey: function(){
        if (this.flowsView != null) this.flowsView.close();
        var el = document.getElementById('sankey-wrapper'),
            type = this.typeSelect.value,
            direction = this.filters['direction'];
        
        var filteredNodes = (type == 'actors') ? this.filters['actors']: 
            (type == 'activities') ? this.filters['activities']: 
            this.filters['groups'];
        
        // pass all known nodes to sankey (not only the filtered ones) to avoid
        // fetching missing nodes
        var collection = (type == 'actors') ? this.actors: 
            (type == 'activities') ? this.activities: 
            this.activityGroups;

        if (!collection) {
            if (type == 'actors')
                el.innerHTML = gettext("The diagram of flows can't be displayed " + 
                    "before limiting the amount of actors by filtering")
            return;
        }
        
        var filterParams = {},
            waste = this.filters['waste'];
        if (waste) filterParams.waste = waste;
        
        // material options for both stocks and flows
        var aggregateMaterials = this.filters['aggregateMaterials'];
        filterParams.materials = {
            aggregate: aggregateMaterials
        }
        var material = this.filters['material'],
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
        
        filteredNodes.forEach(function(node){
            nodeIds.push(node.id);
        })
        
        var levelSuffix = (type == 'activitygroups') ? 'activity__activitygroup__id__in': 
            (type == 'activities') ? 'activity__id__in': 'id__in';
        
        var flowFilters = flowFilterParams['filters'] = [],
            stockFilters = stockFilterParams['filters'] = [],
            origin_filter = {
                'function': 'origin__'+levelSuffix,
                values: nodeIds
            },
            destination_filter = {
                'function': 'destination__'+levelSuffix,
                values: nodeIds
            };
        
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
        
        flowFilterParams.aggregation_level = type;
        stockFilterParams.aggregation_level = type;
            
        this.flowsView = new FlowSankeyView({
            el: el,
            width:  el.clientWidth - 10,
            origins: collection,
            destinations: collection,
            keyflowId: this.keyflowId,
            caseStudyId: this.caseStudy.id,
            materials: this.materials,
            flowFilterParams: flowFilterParams,
            stockFilterParams: stockFilterParams,
            hideUnconnected: true,
            height: 600,
            originTag: type,
            destinationTag: type
        })
    },

    renderSankeyMap: function(){
        var flowMap = new FlowMap("flow-map");
        var collection = this.actors;
        flowMap.renderCsv("/static/data/countries.topo.json", "/static/data/nodes.csv", "/static/data/flows.csv");
        
        //function transformNodes(nodes){
            //var transformed = [];
            //nodes.forEach(function(node)){
                //var t = {
                    //city: node.id,
                    
                //};
                //transformed.append()
            //}
        //}
    },
    
    renderNodeSelectOptions: function(select, collection){
        utils.clearSelect(select);
        option = document.createElement('option');
        option.value = -1; 
        option.text = gettext('All');
        if (collection) option.text += ' (' + collection.length + ')';
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
        else select.disabled = true;
        select.selectedIndex = 0;
        $(select).selectpicker('refresh');
    },

    renderNodeFilters: function(){
        var _this = this;

        this.renderNodeSelectOptions(this.groupSelect, this.activityGroups);
        this.renderNodeSelectOptions(this.activitySelect, this.activities);
        this.renderNodeSelectOptions(this.actorSelect, this.actorsTmp);

        this.groupSelect.addEventListener('change', function(){
            var groupId = this.value;
            // clear filters if 'All' (== -1) is selected, else set specific group
            // and filter activities depending on selection
            _this.filtersTmp['groups'] = (groupId < 0) ? _this.activityGroups: 
                _this.activityGroups.filterBy({'id': groupId});
                
            _this.filtersTmp['activities'] = (groupId < 0) ? _this.activities: 
                _this.activities.filterBy({'activitygroup': groupId});
                
            _this.renderNodeSelectOptions(
                _this.activitySelect,  
                _this.filtersTmp['activities'] || _this.activities
            );
            // filter actors in any case
            _this.filterActors();
        })
        
        this.activitySelect.addEventListener('change', function(){
            var activityId = this.value,
                groupId = _this.groupSelect.value;
            // specific activity is selected
            if (activityId >= 0) {
                _this.filtersTmp['activities']  = _this.activities.filterBy({'id': activityId});
            }
            // clear filter if 'All' (== -1) is selected in both group and activity
            else if (groupId < 0){
                 _this.filtersTmp['activities'] = _this.activities;
            }
            // 'All' is selected for activity but a specific group is selected
            else {
                 _this.filtersTmp['activities'] = _this.activities.filterBy({'activitygroup': groupId});
            }
            // filter actors in any case
            _this.filterActors();
        })
        
        this.actorSelect.addEventListener('change', function(){
            var actorId = this.value,
                selected = this.selectedOptions;
            // multiple actors selected
            _this.filtersTmp['actors'] = [];
            if (selected.length > 1){
                _this.filtersTmp['actors'] = [];
                for (var i = 0; i < selected.length; i++) {
                    var id = selected[i].value;
                    // ignore 'All' in multi select
                    if (id >= 0)
                        _this.filtersTmp['actors'].push(_this.actorsTmp.get(id));
                }
            }
            // single actor selected
            else if (actorId >= 0)
                _this.filtersTmp['actors'].push(_this.actorsTmp.get(actorId));
            // all selected
            else 
                _this.filtersTmp['actors'] = _this.actorsTmp;
        })
    },

    renderMatFilter: function(){
        var _this = this;
        // select material
        var matSelect = document.createElement('div');
        matSelect.classList.add('materialSelect');
        this.hierarchicalSelect(this.materials, matSelect, {
            onSelect: function(model){
                 _this.filtersTmp['material'] = model;
            },
            defaultOption: gettext('All materials')
        });
        this.el.querySelector('#material-filter').appendChild(matSelect);
    }

});
return FlowsView;
}
);