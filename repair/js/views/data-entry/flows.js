define(['views/baseview', 'underscore',
    'views/data-entry/edit-node',
    'collections/activities', 'collections/actors', 'collections/flows', 'collections/stocks',
    'collections/activitygroups', 'collections/publications', 
    'visualizations/sankey', 'views/flowsankey', 'utils/loader'],
function(BaseView, _, EditNodeView, Activities, Actors, Flows, 
    Stocks, ActivityGroups, Publications, Sankey, FlowSankeyView, Loader){

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
    * render view to edit flows of a single keyflow
    *
    * @param {Object} options
    * @param {HTMLElement} options.el                          element the view will be rendered in
    * @param {module:collections/Keyflows.Model} options.model the keyflow (defining the type of flows that will be rendered)
    * @param {module:models/CaseStudy} options.caseStudy       the casestudy
    * @param {module:collections/Materials} options.materials  the available materials
    *
    * @constructs
    * @see http://backbonejs.org/#View
    */
    initialize: function(options){
        _.bindAll(this, 'render');
        _.bindAll(this, 'renderDataTree');
        _.bindAll(this, 'renderDataEntry');
        var _this = this;
        this.template = options.template;
        this.keyflowId = this.model.id;
        this.caseStudy = options.caseStudy;

        this.caseStudyId = this.model.get('casestudy');
        this.materials = options.materials;

        // collections of nodes associated to the casestudy
        this.activityGroups = new ActivityGroups([], {caseStudyId: this.caseStudyId, keyflowId: this.keyflowId});
        this.actors = new Actors([], {caseStudyId: this.caseStudyId, keyflowId: this.keyflowId});
        this.activities = new Activities([], {caseStudyId: this.caseStudyId, keyflowId: this.keyflowId});
        this.publications = new Publications([], { caseStudyId: this.caseStudyId });

        var loader = new Loader(document.getElementById('flows-edit'),
            {disable: true});

        $.when(this.actors.fetch({data: 'included=True'}, 
            this.activityGroups.fetch(), this.activities.fetch(), 
            this.publications.fetch())).then(function(){
        _this.render();
        loader.remove();
        });
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'click #refresh-dataview-btn': 'renderSankey',
        'click a[href="#sankey-tab"]': 'refreshSankey',
        'change #data-view-type-select': 'renderSankey'
    },

    /*
    * render the view
    */
    render: function(){
        if (this.activityGroups.length == 0)
            return;
        var _this = this;
        var html = document.getElementById(this.template).innerHTML
        var template = _.template(html);
        this.el.innerHTML = template({casestudy: this.caseStudy.get('properties').name,
            keyflow: this.model.get('name')});
        this.renderDataTree();
        this.renderSankey();
    },

    refreshSankey: function(){
        if (this.flowsView) 
            this.flowsView.refresh({ width: this.el.offsetWidth - 20});
    },

    renderSankey: function(){
        var type = this.el.querySelector('#data-view-type-select').value;
        var collection = (type == 'actor') ? this.actors: 
            (type == 'activity') ? this.activities: 
            this.activityGroups;
        if (this.flowsView != null) this.flowsView.close();
        this.flowsView = new FlowSankeyView({
            el: this.el.querySelector('#sankey-wrapper'),
            collection: collection,
            materials: this.materials,
            width: this.el.offsetWidth - 20
        })
    },

    /*
    * render the tree with nodes associated to the casestudy
    */
    renderDataTree: function(){
        var _this = this;
        var dataDict = {};
        var activityDict = {};

        this.actors.each(function(actor){
            var node = {
                text: actor.get('name'),
                icon: 'glyphicon glyphicon-user',
                model: actor,
                state: {checked: false}
            };
            var activity_id = actor.get('activity');
            if (!(activity_id in activityDict))
                activityDict[activity_id] = [];
            activityDict[activity_id].push(node);
        });

        this.activityGroups.each(function(group){
            var node = {
                text: group.get('code') + ": " + group.get('name'),
                model: group,
                icon: 'fa fa-cubes',
                nodes: [],
                state: {checked: false}
            };
            dataDict[group.id] = node;
        });

        this.activities.each(function(activity){
            var id = activity.get('id');
            var nodes = (id in activityDict) ? activityDict[id]: [];
            var node = {
                text: activity.get('name'),
                model: activity,
                icon: 'fa fa-cube',
                nodes: nodes,
                state: {checked: false}
            };
            dataDict[activity.get('activitygroup')].nodes.push(node)
        });

        var dataTree = [];
        for (key in dataDict){
            dataTree.push(dataDict[key]);
        };

        // render view on node on click in data-tree
        var onClick = function(event, node){
            _this.renderDataEntry(node, true);
        };
        var divid = '#data-tree';
        require('libs/bootstrap-treeview.min');
        $(divid).treeview({data: dataTree, showTags: true,
            selectedBackColor: '#aad400',
            onNodeSelected: onClick,
            expandIcon: 'glyphicon glyphicon-triangle-right',
            collapseIcon: 'glyphicon glyphicon-triangle-bottom'
            //showCheckbox: true
            });
        $(divid).treeview('collapseAll', {silent: true});
    },

    /*
    * render the edit-view on a node
    */
    renderDataEntry: function(node, check){
        var model = node.model;
        if (model == null)
            return;
        var _this = this;
    
        function renderNode(){
            if (_this.editNodeView != null) _this.editNodeView.close();
            _this.selectedNode = node;
            // currently selected keyflow
            _this.editNodeView = new EditNodeView({
                el: document.getElementById('edit-node'),
                template: 'edit-node-template',
                model: model,
                materials: _this.materials,
                keyflowId: _this.keyflowId,
                keyflowName: _this.model.get('name'),
                caseStudyId: _this.caseStudyId,
                publications: _this.publications,
                onUpload: function() { _this.renderDataEntry(node) } // rerender after upload
            });
        }
    
        if (check && this.editNodeView != null && this.editNodeView.hasChanged()){
            var message = gettext('Attributes of the node have been changed but not uploaded. <br><br>Do you want to discard the changes?');
            this.confirm({ 
                message: message,
                onConfirm: renderNode,
                onCancel: function(){
                    $('#data-tree').treeview('selectNode', [_this.selectedNode.nodeId, { silent: true }]);
                }
            })
        }
        else renderNode();
    }

});
return FlowsView;
});