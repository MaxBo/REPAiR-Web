define(['views/baseview', 'underscore', 'visualizations/flowmap',
        'collections/gdsecollection', 'views/flowsankey', 
        'utils/utils', 'visualizations/map', 'openlayers'],

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
        this.actors = new GDSECollection([], { 
            apiTag: 'actors',
            apiIds: [this.caseStudy.id, this.keyflowId ]
        });
        this.activities = new GDSECollection([], { 
            apiTag: 'activities',
            apiIds: [this.caseStudy.id, this.keyflowId ]
        });
        this.activityGroups = new GDSECollection([], { 
            apiTag: 'activitygroups',
            apiIds: [this.caseStudy.id, this.keyflowId ]
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
                            selDiv = _this.el.querySelector('#area-selections'),
                            levelId = _this.levelSelect.value
                            labels = [],
                            areas = _this.areas[levelId];
                        _this.selectedAreas = [];
                        areaFeats.forEach(function(areaFeat){
                            labels.push(areaFeat.label);
                            _this.selectedAreas.push(areas.get(areaFeat.id))
                        });
                        modalSelDiv.innerHTML = selDiv.innerHTML = labels.join(', ');
                    }
                }
            });
        this.changeAreaLevel();
        
        // event triggered when modal dialog is ready -> trigger rerender to match size
        $(this.areaModal).on('shown.bs.modal', function () {
            _this.areaMap.map.updateSize();
        });
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
        var _this = this;
        if (!_this.selectedAreas) return; // TODO: reset actors
        
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
        this.actors = new GDSECollection([], {
            apiTag: 'filteractors',
            apiIds: [this.caseStudy.id, this.keyflowId]
        })
       // area: geoJSONText, 
        this.loader.activate();
        this.actors.fetch({
            data: { included: 'True' },
            success: function(){
                _this.loader.deactivate();
                console.log(_this.actors);
                _this.renderNodeFilters();
            }
        })
        
    },

    refreshSankeyMap: function(){
        if (this.sankeyMap) this.sankeyMap.refresh();
    },
    
    applyFilters: function(){
        this.filters['activities'] = this.filtersTmp['activities'];
        this.filters['groups'] = this.filtersTmp['groups'];
        this.filters['direction'] = this.el.querySelector('input[name="direction"]:checked').value;
        this.filters['waste'] = this.el.querySelector('select[name="waste"]').value;
        this.filters['aggregate'] = this.el.querySelector('input[name="aggregate"]').checked;
        this.filters['material'] = this.filtersTmp['material'];
        this.renderSankey();
    },
    
    renderSankey: function(){
        var type = this.typeSelect.value;
        var direction = this.filters['direction'];
        var collection = (type == 'actor') ? this.actors: 
            (type == 'activity') ? this.activities: 
            this.activityGroups;
        
        var filtered = (type == 'actor') ? this.actors: 
            (type == 'activity') ? this.filters['activities']: 
            this.filters['groups'];
        
        var filterParams = {},
            waste = this.filters['waste'];
        if (waste) filterParams.waste = waste;
        
        var aggregate = this.filters['aggregate'];
        filterParams.aggregated = aggregate;
        
        var material = this.filters['material'];
        if (material) filterParams.material = material.id;
        
        
        // if the collections are filtered build matching query params for the flows
        var flowFilterParams = Object.assign({}, filterParams);
        var stockFilterParams = Object.assign({}, filterParams);
        
        if (filtered){
            var nodeIds = [];
            filtered.forEach(function(node){
                nodeIds.push(node.id);
            })
            if (nodeIds.length > 0) {
                var queryDirP = (direction == 'both') ? 'nodes': direction;
                flowFilterParams[queryDirP] = nodeIds;
                stockFilterParams.nodes = nodeIds;
            }
        }
        
        if (this.flowsView != null) this.flowsView.close();
        this.flowsView = new FlowSankeyView({
            el: document.getElementById('sankey-wrapper'),
            collection: collection,
            keyflowId: this.keyflowId,
            caseStudyId: this.caseStudy.id,
            materials: this.materials,
            flowFilterParams: flowFilterParams,
            stockFilterParams: stockFilterParams,
            hideUnconnected: true,
            height: 600
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

    renderNodeFilters: function(){
        var _this = this;
        
        function clearOptions(select){
            utils.clearSelect(select);
            option = document.createElement('option');
            option.value = -1; 
            option.text = gettext('All');
            select.appendChild(option);
            select.disabled = true;
        }
        
        function renderOptions(select, collection){
            clearOptions(select);
            collection.forEach(function(model){
                var option = document.createElement('option');
                option.value = model.id;
                option.text = model.get('name');
                select.appendChild(option);
            })
            select.disabled = false;
        }
        
        var groupSelect = this.el.querySelector('select[name="group"]'),
            activitySelect = this.el.querySelector('select[name="activity"]'),
            actorSelect = this.el.querySelector('select[name="actor"]');
            
        renderOptions(groupSelect, this.activityGroups);
        renderOptions(activitySelect, this.activities);
        clearOptions(actorSelect);

        groupSelect.addEventListener('change', function(){
            var groupId = groupSelect.value;
            // set and use filters for selected group, set child activities 
            // clear filter if 'All' (== -1) is selected
            _this.filtersTmp['groups'] = (groupId < 0) ? null: [_this.activityGroups.get(groupId)];
            _this.filtersTmp['activities'] = (groupId < 0) ? null: _this.activities.filterBy({'activitygroup': groupId});
            _this.filtersTmp['actors'] = (groupId < 0) ? null: _this.actors.filterBy({'activitygroup': groupId});
            renderOptions(activitySelect,  _this.filtersTmp['activities'] || _this.activities);
            clearOptions(actorSelect);
        })
        
        activitySelect.addEventListener('change', function(){
            var activityId = activitySelect.value,
                groupId = groupSelect.value;
            // set and use filters for selected activity, set child actors 
            // clear filter if 'All' (== -1) is selected in both group and activity
            if (activityId < 0 && groupId < 0){
                 _this.filtersTmp['activities'] = null;
                _this.filtersTmp['actors']  = null;
                clearOptions(actorSelect);
            }
            // 'All' is selected for activity but a specific group is selected
            else if (activityId < 0){
                 _this.filtersTmp['activities'] = (groupId < 0) ? null: _this.activities.filterBy({'activitygroup': groupId});
                _this.filtersTmp['actors']  = (groupId < 0) ? null: _this.actors.filterBy({'activitygroup': groupId});
                clearOptions(actorSelect);
            }
            // specific activity is selected
            else {
                _this.filtersTmp['activities']  = [_this.activities.get(activityId)];
                _this.filtersTmp['actors']  = _this.actors.filterBy({'activity': activityId});
                renderOptions(actorSelect, _this.filtersTmp['actors']  || _this.actors);
            }
        })
        
        actorSelect.addEventListener('change', function(){
            var activityId = activitySelect.value,
                groupId = groupSelect.value,
                actorId = actorSelect.value;
            // clear filter if 'All' (== -1) is selected in group, activity and 
            if (groupId < 0 && activityId < 0 && actorId < 0){
                _this.filtersTmp['actors'] = null;
            }
            // filter by group if 'All' (== -1) is selected in activity and actor but not group
            if (activityId < 0  && actorId < 0){
                _this.filtersTmp['actors']  = (groupId < 0) ? null: _this.actors.filterBy({'activitygroup': groupId});
            }
            // filter by activity if a specific activity is set and 'All' is selected for actor
            else if (actorId < 0){
                _this.filtersTmp['actors']  = _this.actors.filterBy({'activity': activityId});
            }
            // specific actor
            else
                _this.filtersTmp['actors'] = [_this.actors.get(actorId)];
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