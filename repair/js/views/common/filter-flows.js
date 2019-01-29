define(['views/common/baseview', 'underscore', 'views/common/flows',
        'collections/gdsecollection', 'models/gdsemodel', 'utils/utils',
        'visualizations/map', 'openlayers', 'bootstrap-select'],

function(BaseView, _, FlowsView, GDSECollection, GDSEModel, utils, Map, ol){
/**
*
* @author Christoph Franke
* @name module:views/FilterFlowsView
* @augments module:views/BaseView
*/
var FilterFlowsView = BaseView.extend(
    /** @lends module:views/FilterFlowsView.prototype */
    {

    /**
    * render view to filter flows, calls FlowsView to render filtered flows on map and in sankey
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
        FilterFlowsView.__super__.initialize.apply(this, [options]);
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
            if (options.callback)
                options.callback();
        })

    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'click #area-select-button': 'showAreaSelection',
        'change select[name="area-level-select"]': 'changeAreaLevel',
        'change select[name="node-level-select"]': 'resetNodeSelects',
        'change input[name="show-flow-only"]': 'resetNodeSelects',
        'click .area-filter.modal .confirm': 'confirmAreaSelection',
        'click #apply-filters': 'drawFlows'
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
        if (this.areaLevels.length > 0)
            this.changeAreaLevel();

        // event triggered when modal dialog is ready -> trigger rerender to match size
        $(this.areaModal).on('shown.bs.modal', function () {
            _this.areaMap.map.updateSize();
        });
        this.displayLevelSelect = this.el.querySelector('select[name="display-level-select"]');
        this.nodeLevelSelect = this.el.querySelector('select[name="node-level-select"]');
        this.showFlowOnlyCheck = this.el.querySelector('input[name="show-flow-only"]');
        this.groupSelect = this.el.querySelector('select[name="group"]');
        this.activitySelect = this.el.querySelector('select[name="activity"]');
        this.actorSelect = this.el.querySelector('select[name="actor"]');
        this.flowTypeSelect = this.el.querySelector('select[name="waste"]');
        this.aggregateCheck = this.el.querySelector('input[name="aggregateMaterials"]');
        $(this.groupSelect).selectpicker();
        $(this.activitySelect).selectpicker();
        $(this.actorSelect).selectpicker();
        this.resetNodeSelects();
        this.renderMatFilter();
        this.addEventListeners();
        this.selectedAreas = [];
    },

    drawFlows: function(){
        if (this.flowsView) this.flowsView.close();
        var filter = this.getFilter();
        this.flowsView = new FlowsView({
            el: this.el.querySelector('#flows-render-content'),
            template: 'flows-render-template',
            materials: this.materials,
            actors: this.actors,
            activityGroups: this.activityGroups,
            activities: this.activities,
            caseStudy: this.caseStudy,
            keyflowId: this.keyflowId,
            displayWarnings: true,
            filter: filter
        });
        var displayLevel = this.displayLevelSelect.value;
        this.flowsView.draw(displayLevel);
    },

    resetNodeSelects: function(){
        var level = this.nodeLevelSelect.value,
            hide = [],
            selects = [this.actorSelect, this.groupSelect, this.activitySelect];

        // show the grandparents
        selects.forEach(function(sel){
            sel.parentElement.parentElement.style.display = 'block';
            sel.selectedIndex = 0;
            sel.style.height ='100%'; // resets size, in case it was expanded
        })

        if (level == 'activity'){
            hide = [this.actorSelect];
        }
        if (level == 'activitygroup'){
            hide = [this.actorSelect, this.activitySelect];
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
        this.selectedAreas = [];
        this.el.querySelector('.selections').innerHTML = this.el.querySelector('#area-selections').innerHTML= '';
        this.prepareAreas(levelId);
    },

    prepareAreas: function(levelId, onSuccess){
        var _this = this;
        var areas = this.areas[levelId];
        if (areas){
            this.drawAreas(areas)
            if (onSuccess) onSuccess();
        }
        else {
            areas = new GDSECollection([], {
                apiTag: 'areas',
                apiIds: [ this.caseStudy.id, levelId ]
            });
            this.areas[levelId] = areas;
            //var loader = new utils.Loader(this.areaModal, {disable: true});
            this.loader.activate();
            areas.fetch({
                success: function(){
                    _this.loader.deactivate();
                    _this.drawAreas(areas);
                    if (onSuccess) onSuccess();
                },
                error: function(res) {
                    _this.loader.deactivate();
                    _this.onError(res);
                }
            });
        }
    },

    drawAreas: function(areas){
        var _this = this;
        this.areaMap.clearLayer('areas');
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
        var level = this.nodeLevelSelect.value;
        if (level === 'actor') this.filterActors();
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
        var showFlowOnly = this.showFlowOnlyCheck.checked;
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
                var flowCount = model.get('flow_count');
                if (showFlowOnly && flowCount == 0) return;
                var option = document.createElement('option');
                option.value = model.id;
                option.text = model.get('name') + ' (' + flowCount + ' ' + gettext('flows') + ')';
                if (flowCount == 0) option.classList.add('empty');
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
            }
            // nothing selected anymore -> select 'All'
            if (select.value == null || select.value == ''){
                select.value = -1;
            }
            $(select).selectpicker('refresh');
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
        this.selectedMaterial = null;
        // select material
        var matSelect = document.createElement('div');
        matSelect.classList.add('materialSelect');
        var select = this.el.querySelector('.hierarchy-select');
        this.matSelect = this.hierarchicalSelect(this.materials, matSelect, {
            onSelect: function(model){
                 _this.selectedMaterial = model;
            },
            defaultOption: gettext('All materials'),
            label: function(model, option){
                var flowCount = model.get('flow_count'),
                    label = model.get('name') + ' (' + flowCount + ' ' + gettext('flows') + ')';
                return label;
            }
        });
        var matFlowless = this.materials.filterBy({'flow_count': 0});
        // grey out materials not used in any flows in keyflow
        // (do it afterwards, because hierarchical select is build in template)
        matFlowless.forEach(function(material){
            var li = _this.matSelect.querySelector('li[data-value="' + material.id + '"]'),
                a = li.querySelector('a');
            a.classList.add('empty');
        })
        this.el.querySelector('#material-filter').appendChild(matSelect);
    },

    // return a model representing the current filter settings
    // overwrites properties of given filter or creates a new one, if not given
    getFilter: function(filter){
        var filter = filter || new GDSEModel();
        filter.set('area_level', this.areaLevelSelect.value);
        var material = this.selectedMaterial;
        filter.set('material', (material) ? material.id : null);
        var direction = this.el.querySelector('input[name="direction"]:checked').value;
        filter.set('direction', direction);
        filter.set('aggregate_materials', this.aggregateCheck.checked)
        filter.set('flow_type', this.flowTypeSelect.value);

        var areas = [];
        this.selectedAreas.forEach(function(area){
            areas.push(area.id)
        })
        filter.set('areas', areas);

        // get the nodes by level
        // check descending from actors, where sth is selected
        // take this as the actual level
        var levelSelects = [this.actorSelect, this.activitySelect, this.groupSelect],
            nodeLevels = ['actor', 'activity', 'activitygroup'],
            nodeLevel = 'activitygroup',
            selectedNodes = [],
            levelIdx = nodeLevels.indexOf(this.nodeLevelSelect.value); // start at selected level, ignore more granular ones

        for(var i = levelIdx; i < levelSelects.length; i++){
            var select = levelSelects[i];
            nodeLevel = nodeLevels[i];
            // sth is selected
            if (select.value >= 0){
                selectedNodes = this.getSelectedNodes(select);
                break;
            }
        }
        filter.set('filter_level', nodeLevel);
        filter.set('node_ids', selectedNodes.join(','));
        return filter;
    },

    applyFilter: function(filter){
        var _this = this
            areaLevel = filter.get('area_level'),
            areas = filter.get('areas');
        this.showFlowOnlyCheck.checked = false;
        if (this.flowsView) this.flowsView.close();

        this.nodeLevelSelect.value = filter.get('filter_level').toLowerCase();
        this.resetNodeSelects();

        if (areaLevel == null) {
            this.areaLevelSelect.selectedIndex = 0;
            this.changeAreaLevel();
        }
        else {
            this.areaLevelSelect.value = areaLevel;
            var labels = [];
            if (areas && areas.length > 0) {
                this.prepareAreas(areaLevel, function(){
                    areas.forEach(function(areaId){
                        var area = _this.areas[areaLevel].get(areaId);
                        _this.areaMap.selectFeature('areas', areaId);
                        labels.push(area.get('name'));
                        var areasLabel = labels.join(', ');
                        _this.el.querySelector('.selections').innerHTML = areasLabel;
                        _this.el.querySelector('#area-selections').innerHTML = areasLabel;
                    })
                });
            }
            else _this.changeAreaLevel();
        }

        var direction = filter.get('direction'),
            directionOption = document.querySelector('input[name="direction"][value="' + direction.toLowerCase() + '"]')
        directionOption.checked = true;
        this.flowTypeSelect.value = filter.get('flow_type').toLowerCase();
        this.aggregateCheck.checked = filter.get('aggregate_materials');

        // hierarchy-select plugin offers no functions to set (actually no functions at all) -> emulate clicking on row
        var material = filter.get('material'),
            li = this.matSelect.querySelector('li[data-value="' + material + '"]');
        if(li){
            matItem = li.querySelector('a');
            matItem.click();
        }
        // click first one, if no material
        else{
            this.matSelect.querySelector('a').click();
        }

        // level actor -> filter actors
        var nodeLevel = filter.get('filter_level').toLowerCase(),
            nodeIds = filter.get('node_ids');
        this.resetNodeSelects();
        if(nodeIds) {
            this.nodeLevelSelect.value = nodeLevel;
            var select;
            // actors are special, they are not fetched in bulk and most likely unknown yet
            if (nodeLevel === 'actor'){
                select = this.actorSelect;
                this.actors.fetch(
                    {
                        data: { 'id__in': nodeIds, fields: ['id', 'name'].join() },
                        success: function(){
                            _this.renderNodeSelectOptions(select, _this.actors);
                            // could also just select all of them
                            $(select).selectpicker('val', nodeIds.split(','));
                        },
                        error: _this.onError
                    }
                );
            }
            else{
                select = (nodeLevel === 'activity') ? this.activitySelect : this.groupSelect;
                $(select).selectpicker('val', nodeIds.split(','))
            }
        }
    },

    close: function(){
        if (this.flowsView) this.flowsView.close();
        FilterFlowsView.__super__.close.call(this);
    }

});
return FilterFlowsView;
}
);
