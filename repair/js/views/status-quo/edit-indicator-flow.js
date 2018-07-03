define(['views/baseview', 'underscore', 'collections/gdsecollection', 
        'views/flowsankey', 'utils/utils', 'bootstrap-select',
        'bootstrap-tagsinput'],

function(BaseView, _, GDSECollection, FlowSankeyView, utils){
/**
*
* @author Christoph Franke
* @name module:views/IndicatorFlowEditView
* @augments module:views/BaseView
*/
var IndicatorFlowEditView = BaseView.extend(
    /** @lends module:views/FlowsView.prototype */
    {

    /**
    * render view on flow (A or B) settings for indicators
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
        IndicatorFlowEditView.__super__.initialize.apply(this, [options]);
        _.bindAll(this, 'resetNodeSelects');
        this.activityGroups = options.activityGroups;
        this.activities = options.activities;
        this.materials = options.materials;
        this.caseStudy = options.caseStudy;
        this.keyflowId = options.keyflowId;
        this.indicatorFlow = options.indicatorFlow;

        this.originActors = new GDSECollection([], {
            apiTag: 'actors',
            apiIds: [this.caseStudy.id, this.keyflowId],
            comparator: 'name'
        })
        this.destinationActors = new GDSECollection([], {
            apiTag: 'actors',
            apiIds: [this.caseStudy.id, this.keyflowId],
            comparator: 'name'
        })

        this.render();
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'click #render-sankey': 'renderSankey'
    },
    
    render: function(){
        var _this = this;
        var html = document.getElementById(this.template).innerHTML
        var template = _.template(html);
        this.el.innerHTML = template();
        
        this.originSelects = {
            levelSelect: this.el.querySelector('select[name="origin-level-select"]'),
            groupSelect: this.el.querySelector('select[name="origin-group"]'),
            activitySelect: this.el.querySelector('select[name="origin-activity"]'),
            actorSelect: this.el.querySelector('select[name="origin-actor"]')
        }
        
        this.destinationSelects = {
            levelSelect: this.el.querySelector('select[name="destination-level-select"]'),
            groupSelect: this.el.querySelector('select[name="destination-group"]'),
            activitySelect: this.el.querySelector('select[name="destination-activity"]'),
            actorSelect: this.el.querySelector('select[name="destination-actor"]')
        }
        
        this.typeSelect = this.el.querySelector('select[name="waste"]');
        
        $(this.originSelects.groupSelect).selectpicker();
        $(this.originSelects.activitySelect).selectpicker();
        $(this.originSelects.actorSelect).selectpicker();
        $(this.destinationSelects.groupSelect).selectpicker();
        $(this.destinationSelects.activitySelect).selectpicker();
        $(this.destinationSelects.actorSelect).selectpicker();
        
        this.originSelects.levelSelect.addEventListener(
            'change', function(){ _this.resetNodeSelects('origin') })
        this.destinationSelects.levelSelect.addEventListener(
            'change', function(){ _this.resetNodeSelects('destination') })
        
        this.addEventListeners('origin');
        this.addEventListeners('destination');
        this.renderMatFilter();
        
        this.materialTags = this.el.querySelector('input[name="material-tags"]');
        $(this.materialTags).tagsinput({
            itemValue: 'value',
            itemText: 'text'
        })
        // hide the input of tags
        this.materialTags.parentElement.querySelector('.bootstrap-tagsinput>input').style.display = 'none';
        
        this.setInputs(this.indicatorFlow);
    },
    
    // filter and fetch the actors by selected group/activity
    // tag indicates the select group ('origin' or 'destination')
    filterActors: function(tag){
        var _this = this,
            geoJSONText, 
            queryParams = { 
                included: 'True', 
                fields: ['id', 'name'].join() 
            };
        
        var selectGroup = (tag == 'origin') ? this.originSelects : this.destinationSelects,
            actors = (tag == 'origin') ? this.originActors : this.destinationActors,
            activity = selectGroup.activitySelect.value,
            group = selectGroup.groupSelect.value;

        if(activity >= 0) queryParams['activity'] = activity;
        else if (group >= 0) queryParams['activity__activitygroup'] = group;

       // area: geoJSONText, 
        this.loader.activate({offsetX: '20%'});
        actors.fetch({
            data: queryParams,
            success: function(response){
                _this.loader.deactivate();
                actors.sort();
                _this.renderNodeSelectOptions(selectGroup.actorSelect, actors);
                selectGroup.actorSelect.value = -1;
            },
            reset: true
        })
        
    },

    // add the event listeners to the group/activity selects
    // tag indicates the select group ('origin' or 'destination')
    addEventListeners: function(tag){
        var _this = this;
        var selectGroup = (tag == 'origin') ? this.originSelects : this.destinationSelects;

        selectGroup.groupSelect.addEventListener('change', function(){
            var level = selectGroup.levelSelect.value;
            if (level == 'group') return;
            var groupId = this.value;
            filteredActivities = (groupId < 0) ? _this.activities: 
                _this.activities.filterBy({'activitygroup': groupId});
                
            _this.renderNodeSelectOptions(selectGroup.activitySelect, filteredActivities);
            if (level == 'actor')
                _this.filterActors(tag);
        })
        
        selectGroup.activitySelect.addEventListener('change', function(){
            // render actors only if their level is selected
            if (selectGroup.levelSelect.value == 'actor') 
                _this.filterActors(tag);
        })
    },
    
    // reset the options of the selects
    // tag indicates the select group ('origin' or 'destination')
    resetNodeSelects: function(tag){
        
        var selectGroup = (tag == 'origin') ? this.originSelects : this.destinationSelects,
            level = selectGroup.levelSelect.value,
            multi, 
            hide = [],
            selects = [selectGroup.actorSelect, selectGroup.groupSelect, selectGroup.activitySelect];
            
            
         selects.forEach(function(sel){
            sel.parentElement.parentElement.style.display = 'block';
            sel.selectedIndex = 0;
            sel.removeAttribute('multiple');
            sel.style.height ='100%'; // resets size, in case it was expanded
        })
        if (level == 'actor'){
            multi = selectGroup.actorSelect;
        }
        else if (level == 'activity'){
            multi = selectGroup.activitySelect;
            hide = [selectGroup.actorSelect];
        }
        else {
            multi = selectGroup.groupSelect;
            hide = [selectGroup.actorSelect, selectGroup.activitySelect];
        }
        multi.setAttribute('multiple', true);
        $(multi).selectpicker("refresh");
        hide.forEach(function(s){
            s.parentElement.parentElement.style.display = 'none';
        })
        this.renderNodeSelectOptions(selectGroup.groupSelect, this.activityGroups);
        if(level != 'group')
            this.renderNodeSelectOptions(selectGroup.activitySelect, this.activities);
        if(level == 'actor')
            this.renderNodeSelectOptions(selectGroup.actorSelect);
        
        // selectpicker has to be completely rerendered to change between
        // multiple and single select
        selects.forEach(function(sel){
            $(sel).selectpicker('destroy');
            $(sel).selectpicker();
        });
    },

    // fill given select with options created based on models of given collection
    renderNodeSelectOptions: function(select, collection){
        utils.clearSelect(select);
        option = document.createElement('option');
        option.value = -1;
        option.text = gettext('All');
        select.appendChild(option);
        if (collection) option.text += ' (' + collection.length + ')';
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
    
    // render the material filter
    renderMatFilter: function(){
        var _this = this;
        // select material
        var matSelect = document.createElement('div');
        matSelect.classList.add('materialSelect');
        this.hierarchicalSelect(this.materials, matSelect, {
            onSelect: function(model){
                if (model)
                    $(_this.materialTags).tagsinput('add', { 
                        "value": model.id , "text": model.get('name')
                    });
            },
            defaultOption: gettext('Select')
        });
        this.el.querySelector('.material-filter').appendChild(matSelect);
    },
    
    // get selected nodes in given select group depending on selected node level
    getSelectedNodes: function(selectGroup){
        var level = selectGroup.levelSelect.value,
            nodeSelect = (level == 'actor') ? selectGroup.actorSelect: 
                         (level == 'activity') ? selectGroup.activitySelect: 
                         selectGroup.groupSelect;

        function getValues(selectOptions){
            var values = [];
            for (var i = 0; i < selectOptions.length; i++) {
                var id = selectOptions[i].value;
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
        else return getValues(nodeSelect.options)
    },
    
    // preset the selected nodes in given select group depending on selected node level
    setSelectedNodes: function(selectGroup, values, actors){
        if (values.length == 0 || values[0].length == 0)
            return;
        var level = selectGroup.levelSelect.value,
            nodeSelect = (level == 'actor') ? selectGroup.actorSelect: 
                         (level == 'activity') ? selectGroup.activitySelect: 
                         selectGroup.groupSelect,
            _this = this;
        if (level == 'actor') {
            actors.fetch({
                data: {
                    'id__in': values.join(',')
                },
                success: function(){
                    _this.renderNodeSelectOptions(nodeSelect, actors);
                    $(nodeSelect).selectpicker('val', values);
                },
                error: _this.onError
            })
            return;
        }
        $(nodeSelect).selectpicker('val', values);
    },
    
    // get the selected materials
    selectedMaterials: function(){
        var tags = $(this.materialTags).tagsinput('items'),
            materialIds = [];
        tags.forEach(function(item){
            materialIds.push(item.value)
        })
        return materialIds;
    },
    
    // preset the selected materials
    setSelectedMaterials: function(materialIds){
        var tags = $(this.materialTags).tagsinput('items'),
            _this = this;
        materialIds.forEach(function(materialId){
            var model = _this.materials.get(materialId);
            $(_this.materialTags).tagsinput('add', { 
                "value": model.id , "text": model.get('name')
            });
        });
    },
    
    // render the sankey diagram
    renderSankey: function(){
        if (this.flowsView != null) this.flowsView.close();
        var el = this.el.querySelector('.sankey-wrapper'),
            originLevel = this.originSelects.levelSelect.value,
            destinationLevel = this.destinationSelects.levelSelect.value;
        
        var origins = (originLevel == 'actor') ? this.originActors: 
            (originLevel == 'activity') ? this.activities: 
            this.activityGroups;
        var destinations = (destinationLevel == 'actor') ? this.destinationActors: 
            (destinationLevel == 'activity') ? this.activities: 
            this.activityGroups;

        var filterParams = {},
            waste = (this.typeSelect.value == 'waste') ? true : 
                    (this.typeSelect.value == 'product') ? false : '';
        if (waste) filterParams.waste = waste;
        
        var materialIds = this.selectedMaterials();
        
        if (materialIds.length > 0) 
            filterParams.materials = { 
                ids: materialIds,
                aggregate: true
            };
        
        var originNodeIds = this.getSelectedNodes(this.originSelects),
            destinationNodeIds = this.getSelectedNodes(this.destinationSelects);
        
        var originSuffix = (originLevel == 'activitygroup') ? 'activity__activitygroup__id__in': 
                (originLevel == 'activity') ? 'activity__id__in': 'id__in',
            destinationSuffix = (destinationLevel == 'activitygroup') ? 'activity__activitygroup__id__in': 
                (destinationLevel == 'activity') ? 'activity__id__in': 'id__in';
        
        var filters = filterParams['filters'] = [];
        if (originNodeIds.length > 0)
            filters.push({
                'function': 'origin__'+originSuffix,
                values: originNodeIds
            });
        
        if (destinationNodeIds.length > 0)
            filters.push({
                'function': 'destination__'+destinationSuffix,
                values: destinationNodeIds
            });
        
        // flow origins and destinations have to be in selected subsets (AND linked, in contrast to FlowsView where you have directions to/from the selected nodes)
        filterParams['filter_link'] = 'and';
        
        this.flowsView = new FlowSankeyView({
            el: el,
            width:  el.clientWidth - 10,
            origins: origins,
            destinations: destinations,
            keyflowId: this.keyflowId,
            caseStudyId: this.caseStudy.id,
            materials: this.materials,
            flowFilterParams: filterParams,
            renderStocks: false,
            hideUnconnected: true,
            forceSideBySide: true,
            height: 600
        })
    },
    
    // preset all inputs based on flow data
    setInputs: function(flow){
        if (flow == null) return;
        var materialIds = flow.materials || [],
            originNodeIds = flow.origin_node_ids || "",
            destinationNodeIds = flow.destination_node_ids || "",
            originLevel = flow.origin_node_level || 'actor',
            destinationLevel = flow.destination_node_level || 'actor',
            flowType = flow.flow_type || 'both',
            spatial = flow.spatial_application || 'none';
        
        this.originSelects.levelSelect.value = originLevel.toLowerCase();
        this.destinationSelects.levelSelect.value = destinationLevel.toLowerCase();
        this.resetNodeSelects('origin');
        this.resetNodeSelects('destination');
        this.setSelectedNodes(this.originSelects, originNodeIds.split(','), this.originActors);
        this.setSelectedNodes(this.destinationSelects, destinationNodeIds.split(','), this.destinationActors);
        this.typeSelect.value = flowType.toLowerCase();
        this.setSelectedMaterials(materialIds);
        
        this.el.querySelector('input[name="spatial-filtering"][value="' + spatial.toLowerCase() + '"]').checked = true;
    },
    
    // get the flow with currently set values
    getInputs: function(){
        var materialIds = this.selectedMaterials(),
            originNodeIds = this.getSelectedNodes(this.originSelects),
            destinationNodeIds = this.getSelectedNodes(this.destinationSelects),
            originLevel = this.originSelects.levelSelect.value,
            destinationLevel = this.destinationSelects.levelSelect.value,
            flowType = this.typeSelect.value,
            spatial = this.el.querySelector('input[name="spatial-filtering"]:checked').value;
            
        var flow = {
            origin_node_level: originLevel,
            origin_node_ids: originNodeIds.join(','),
            destination_node_level: destinationLevel,
            destination_node_ids: destinationNodeIds.join(','),
            materials: materialIds,
            flow_type: flowType,
            spatial_application: spatial
        }
        
        return flow;
    },
    
    close: function(){
        IndicatorFlowEditView.__super__.close();
        this.flowsView.close();
    }

});
return IndicatorFlowEditView;
}
);