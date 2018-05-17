define(['views/baseview', 'underscore', 'visualizations/flowmap',
        'collections/gdsecollection', 'views/flowsankey', 
        'utils/utils'],

function(BaseView, _, FlowMap, GDSECollection, FlowSankeyView, utils){
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
        _.bindAll(this, 'refreshMap');

        this.template = options.template;
        this.caseStudy = options.caseStudy;
        this.keyflowId = options.keyflowId;
        this.filterParams = {};
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
        this.loader.activate();
        var params = { included: 'True' },
            promises = [
                this.actors.fetch({ data: params }), 
                this.activities.fetch(),
                this.activityGroups.fetch(),
                this.materials.fetch()
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
        'change select[name="waste"]': 'renderSankey',
        'change input[name="direction"]': 'renderSankey',
        'change #data-view-type-select': 'renderSankey',
    },

    /*
    * render the view
    */
    render: function(){
        var _this = this;
        var html = document.getElementById(this.template).innerHTML
        var template = _.template(html);
        this.el.innerHTML = template();
        this.typeSelect = this.el.querySelector('#data-view-type-select');
        this.renderMatFilter();
        this.renderNodeFilters();
        this.renderSankey();
    },

    refreshMap: function(){
        if (this.sankeyMap) this.sankeyMap.refresh();
    },

    renderSankey: function(){
        var type = this.typeSelect.value;
        var direction = this.el.querySelector('input[name="direction"]:checked').value;
        var collection = (type == 'actor') ? this.actors: 
            (type == 'activity') ? this.activities: 
            this.activityGroups;
        
        var filtered = (type == 'actor') ? this.actorsFiltered: 
            (type == 'activity') ? this.activitiesFiltered: 
            this.activityGroupsFiltered;
            
        var waste = this.el.querySelector('select[name="waste"]').value;
        this.filterParams.waste = waste;
        if (waste == '') delete this.filterParams.waste
        
        // if the collections are filtered build matching query params for the flows
        var flowFilterParams = Object.assign({}, this.filterParams);
        var stockFilterParams = Object.assign({}, this.filterParams);
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
            _this.activityGroupsFiltered = (groupId < 0) ? null: [_this.activityGroups.get(groupId)];
            _this.activitiesFiltered = (groupId < 0) ? null: _this.activities.filterBy({'activitygroup': groupId});
            _this.actorsFiltered = (groupId < 0) ? null: _this.actors.filterBy({'activitygroup': groupId});
            renderOptions(activitySelect, _this.activitiesFiltered || _this.activities);
            clearOptions(actorSelect);
            _this.typeSelect.value = 'activitygroup';
            _this.renderSankey();
        })
        
        activitySelect.addEventListener('change', function(){
            var activityId = activitySelect.value,
                groupId = groupSelect.value;
            // set and use filters for selected activity, set child actors 
            // clear filter if 'All' (== -1) is selected in both group and activity
            if (activityId < 0 && groupId < 0){
                _this.activitiesFiltered = null;
                _this.actorsFiltered = null;
                clearOptions(actorSelect);
            }
            // 'All' is selected for activity but a specific group is selected
            else if (activityId < 0){
                _this.activitiesFiltered = (groupId < 0) ? null: _this.activities.filterBy({'activitygroup': groupId});
                _this.actorsFiltered = (groupId < 0) ? null: _this.actors.filterBy({'activitygroup': groupId});
                clearOptions(actorSelect);
            }
            // specific activity is selected
            else {
                _this.activitiesFiltered = [_this.activities.get(activityId)];
                _this.actorsFiltered = _this.actors.filterBy({'activity': activityId});
                renderOptions(actorSelect, _this.actorsFiltered || _this.actors);
            }
            _this.typeSelect.value = 'activity';
            _this.renderSankey();
        })
        
        actorSelect.addEventListener('change', function(){
            var activityId = activitySelect.value,
                groupId = groupSelect.value,
                actorId = actorSelect.value;
            // clear filter if 'All' (== -1) is selected in group, activity and 
            if (groupId < 0 && activityId < 0 && actorId < 0){
                _this.actorsFiltered = null;
            }
            // filter by group if 'All' (== -1) is selected in activity and actor but not group
            if (activityId < 0  && actorId < 0){
                _this.actorsFiltered = (groupId < 0) ? null: _this.actors.filterBy({'activitygroup': groupId});
            }
            // filter by activity if a specific activity is set and 'All' is selected for actor
            else if (actorId < 0){
                _this.actorsFiltered = _this.actors.filterBy({'activity': activityId});
            }
            // specific actor
            else
                _this.actorsFiltered = [_this.actors.get(actorId)];
            _this.typeSelect.value = 'actor'
            _this.renderSankey();
        })
    },

    renderMatFilter: function(){
        var _this = this;
        // select material
        var matSelect = document.createElement('div');
        matSelect.classList.add('materialSelect');
        this.hierarchicalSelect(this.materials, matSelect, {
            onSelect: function(model){
                 var modelId = (model) ? model.id : null;
                 _this.filterParams.material = modelId;
                 if (modelId == null) delete _this.filterParams.material;
                _this.renderSankey();
            },
            defaultOption: gettext('All materials')
        });
        this.el.querySelector('#material-filter').appendChild(matSelect);
    }

});
return FlowsView;
}
);