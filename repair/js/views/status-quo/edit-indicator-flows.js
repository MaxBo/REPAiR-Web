define(['views/baseview', 'underscore', 'collections/gdsecollection', 
        'views/flowsankey', 'utils/utils'],

function(BaseView, _, GDSECollection, FlowSankeyView, utils){
/**
*
* @author Christoph Franke
* @name module:views/IndicatorFlowsEditView
* @augments module:views/BaseView
*/
var IndicatorFlowsEditView = BaseView.extend(
    /** @lends module:views/FlowsView.prototype */
    {

    /**
    * render view on flow (A/B) settings for indicators
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
        IndicatorFlowsEditView.__super__.initialize.apply(this, [options]);
        _.bindAll(this, 'resetNodeSelects');
        this.activityGroups = options.activityGroups;
        this.activities = options.activities;
        this.materials = options.materials;
        this.caseStudy = options.caseStudy;
        this.keyflowId = options.keyflowId;

        this.actors = new GDSECollection([], {
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
        
        this.levelSelect = this.el.querySelector('select[name="level-select"]');
        this.groupSelect = this.el.querySelector('select[name="group"]');
        this.activitySelect = this.el.querySelector('select[name="activity"]');
        this.actorSelect = this.el.querySelector('select[name="actor"]');

        this.levelSelect.addEventListener('change', _this.resetNodeSelects)

        this.levelSelect.value = 'actor';
        this.resetNodeSelects();
        this.selectEvents();
        this.renderMatFilter();
    },
    
    filterActors: function(){
        var _this = this,
            geoJSONText, 
            queryParams = { 
                included: 'True', 
                fields: ['id', 'name'].join() 
            };
            
        var activity = this.activitySelect.value,
            group = this.groupSelect.value;

        if(activity >= 0) queryParams['activity'] = activity;
        else if (group >= 0) queryParams['activity__activitygroup'] = group;

       // area: geoJSONText, 
        this.loader.activate({offsetX: '20%'});
        this.actors.fetch({
            data: queryParams,
            success: function(response){
                _this.loader.deactivate();
                _this.actors.sort();
                _this.renderNodeSelectOptions(_this.actorSelect, _this.actors);
                _this.actorSelect.value = -1;
            },
            reset: true
        })
        
    },

    selectEvents: function(){
        var _this = this;

        this.groupSelect.addEventListener('change', function(){
            var level = _this.levelSelect.value;
            if (level == 'group') return;
            var groupId = this.value;
            filteredActivities = (groupId < 0) ? _this.activities: 
                _this.activities.filterBy({'activitygroup': groupId});
                
            _this.renderNodeSelectOptions(_this.activitySelect, filteredActivities);
            if (level == 'actor')
                _this.filterActors();
        })
        
        this.activitySelect.addEventListener('change', function(){
            if (_this.levelSelect.value == 'actor') 
                _this.filterActors();
        })
    },
    
    resetNodeSelects: function(){
        
        var level = this.levelSelect.value,
            multi, 
            hide = [];
            
         [this.actorSelect, this.groupSelect, this.activitySelect].forEach(function(sel){
            sel.parentElement.style.display = 'block';
            sel.selectedIndex = 0;
            sel.removeAttribute('multiple');
            sel.style.height ='100%'; // resets size, in case it was expanded
        })
        if (level == 'actor'){
            multi = this.actorSelect;
        }
        else if (level == 'activity'){
            multi = this.activitySelect;
            hide = [this.actorSelect];
        }
        else {
            multi = this.groupSelect;
            hide = [this.actorSelect, this.activitySelect];
        }
        multi.setAttribute('multiple', true);
        hide.forEach(function(s){
            s.parentElement.style.display = 'none';
        })
        // if group is selected you won't see activities anyway so just leave it
        // as it is
        if(level != 'group')
            this.renderNodeSelectOptions(this.activitySelect, this.activities);
        this.renderNodeSelectOptions(this.groupSelect, this.activityGroups);
        this.renderNodeSelectOptions(this.actorSelect);
        
    },

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
    },
    
    renderMatFilter: function(){
        var _this = this;
        // select material
        var matSelect = document.createElement('div');
        matSelect.classList.add('materialSelect');
        this.hierarchicalSelect(this.materials, matSelect, {
            onSelect: function(model){
                 _this.material = model;
            },
            defaultOption: gettext('All materials')
        });
        this.el.querySelector('.material-filter').appendChild(matSelect);
    },
    
    renderSankey: function(){
        if (this.flowsView != null) this.flowsView.close();
        var el = this.el.querySelector('.sankey-wrapper'),
            type = this.levelSelect.value;
        
        var collection = (type == 'actor') ? this.actors: 
            (type == 'activity') ? this.activities: 
            this.activityGroups;
        
        var level = (type == 'actor') ? 'actors': 
            (type == 'activity') ? 'activities': 
            'activitygroups';

        if (!collection) {
            if (type == 'actors')
                el.innerHTML = gettext("The diagram of flows can't be displayed " + 
                    "before limiting the amount of actors by filtering")
            return;
        }
        
        var filterParams = {},
            waste = this.el.querySelector('select[name="waste"]').value;
        if (waste) filterParams.waste = waste;
        
        var material = this.material;
        if (material) filterParams.material = {id: material.id};
        
        var nodeSelect = (type == 'actor') ? this.actorSelect: 
            (type == 'activity') ? this.activitySelect: 
            this.groupSelect;
        
        if (nodeSelect.value >= 0){
            var nodeIds = [];
            selected = nodeSelect.selectedOptions;
            for (var i = 0; i < selected.length; i++) {
                var id = selected[i].value;
                // ignore 'All' in multi select
                if (id >= 0)
                    nodeIds.push(id);
            }
            
            filterParams['subset'] = {};
            filterParams['subset'][level] = nodeIds;
        }
        
        filterParams.aggregation_level = level;
            
        this.flowsView = new FlowSankeyView({
            el: el,
            width:  el.clientWidth - 10,
            collection: collection,
            keyflowId: this.keyflowId,
            caseStudyId: this.caseStudy.id,
            materials: this.materials,
            flowFilterParams: filterParams,
            renderStocks: false,
            hideUnconnected: true,
            height: 600,
            tag: level,
            sourceToSinkPresentation: true
        })
    },
    
    close: function(){
        this.flowsView.close();
    }

});
return IndicatorFlowsEditView;
}
);