define(['views/common/baseview', 'underscore',
        'views/data-entry/edit-node', 'views/common/filter-flows',
        'collections/gdsecollection', 'models/gdsemodel',
        'app-config', 'patternfly-bootstrap-treeview',
        'datatables.net-bs',
        'datatables.net-bs/css/dataTables.bootstrap.css',
        'datatables.net-buttons-bs/css/buttons.bootstrap.min.css',
        'patternfly-bootstrap-treeview/dist/bootstrap-treeview.min.css'],
function(BaseView, _, EditNodeView, FlowsView, GDSECollection, GDSEModel, config){

/**
*
* @author Christoph Franke
* @name module:views/FlowsEditView
* @augments module:views/BaseView
*/
var FlowsEditView = BaseView.extend(
    /** @lends module:views/FlowsEditView.prototype */
    {

    /**
    * render view to edit flows of a single keyflow
    *
    * @param {Object} options
    * @param {HTMLElement} options.el                          element the view will be rendered in
    * @param {module:collections/Keyflows.Model} options.model the keyflow (defining the type of flows that will be rendered)
    * @param {module:models/CaseStudy} options.caseStudy       the casestudy
    * @param {module:collections/Materials} options.materials  the available materials
    * @param {module:collections/GDSECollection} options.activities  the activities in the keyflow
    *
    * @constructs
    * @see http://backbonejs.org/#View
    */
    initialize: function(options){
        FlowsEditView.__super__.initialize.apply(this, [options]);
        _.bindAll(this, 'renderDataTree');
        _.bindAll(this, 'renderNodeView');
        var _this = this;
        this.template = options.template;
        this.keyflowId = this.model.id;
        this.caseStudy = options.caseStudy;

        this.caseStudyId = this.model.get('casestudy');
        this.materials = options.materials;

        // collections of nodes associated to the casestudy
        this.activityGroups = new GDSECollection([], {
            apiTag: 'activitygroups',
            apiIds: [ this.caseStudyId, this.keyflowId ]
        });
        this.activities = options.activities;
        this.publications = new GDSECollection([], {
            apiTag: 'publicationsInCasestudy',
            apiIds: [ this.caseStudyId ]
        });

        this.loader.activate();

        var promises = [ this.activityGroups.fetch(), this.publications.fetch() ]
        Promise.all(promises).then(function(){
            _this.loader.deactivate();
            _this.render();
        });
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

    renderSankey: function(){
        var flowsView = new FlowsView({
            caseStudy: this.caseStudy,
            el: this.el.querySelector('#sankey-tab'),
            template: 'filter-flows-template',
            keyflowId: this.keyflowId
        })
    },

    /*
    * render the tree with nodes associated to the casestudy
    */
    renderDataTree: function(){
        var _this = this;
        var dataDict = {};

        this.activityGroups.each(function(group){
            var node = {
                text: group.get('code') + ": " + group.get('name'),
                model: group,
                icon: 'fa fa-cubes',
                nodes: []
            };
            dataDict[group.id] = node;
        });

        this.activities.each(function(activity){
            var id = activity.get('id');
            var node = {
                text: activity.get('name'),
                model: activity,
                icon: 'fa fa-cube'
            };
            dataDict[activity.get('activitygroup')].nodes.push(node)
        });

        var dataTree = [];
        for (key in dataDict){
            dataTree.push(dataDict[key]);
        };

        // render view on node on click in data-tree
        var onClick = function(event, node){
            // check and warn if previous view was changed
            if (_this.editNodeView != null && _this.editNodeView.hasChanged()){
                var message = gettext('Attributes of the node have been changed but not uploaded. <br><br>Do you want to discard the changes?');
                _this.confirm({
                    message: message,
                    onConfirm: function(){
                        _this.renderNodeView(node);
                    },
                    onCancel: function(){
                        $('#data-tree').treeview('selectNode', [_this.selectedNode, { silent: true }]);
                    }
                })
            }
            else _this.renderNodeView(node);
        };
        var divid = '#data-tree';
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
    renderNodeView: function(node, options){
        var options = options || {},
            model = node.model,
            _this = this;
        if (_this.editNodeView != null) _this.editNodeView.close();
        _this.selectedNode = node;
        model.caseStudyId = _this.caseStudyId;
        model.keyflowId = _this.keyflowId;
        model.fetch({
            success: function(){
                // currently selected keyflow
                _this.editNodeView = new EditNodeView({
                    el: document.getElementById('edit-node'),
                    template: 'edit-node-template',
                    model: model,
                    materials: _this.materials,
                    keyflowId: _this.keyflowId,
                    caseStudyId: _this.caseStudyId,
                    publications: _this.publications,
                    onUpload: function() { _this.renderNodeView(node, { rerender: true }) } // rerender after upload
                });
            }, error: _this.onError
        })
    },

});
return FlowsEditView;
});
