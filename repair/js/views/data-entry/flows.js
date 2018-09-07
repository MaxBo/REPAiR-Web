define(['views/common/baseview', 'underscore',
        'views/data-entry/edit-node', 'views/status-quo/flows',
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
        'click #actor-select-modal .confirm': 'confirmActorSelection'
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
        this.setupActorsTable();
    },

    renderSankey: function(){
        var flowsView = new FlowsView({
            caseStudy: this.caseStudy,
            el: this.el.querySelector('#sankey-tab'),
            template: 'flows-template',
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
            var actorPlaceholder  = {
                model: null,
                parentActivityId: id,
                text: [gettext('Select Actor')],
                tag: 'actorSelect',
                icon: 'fa fa-users'
            };
            var node = {
                text: activity.get('name'),
                model: activity,
                icon: 'fa fa-cube',
                nodes: [actorPlaceholder]
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

    setupActorsTable: function(){
        var _this = this;
        var columns = [
            {data: 'id', title: 'ID', visible: false},
            {data: 'name', title: gettext('Name')},
            {data: 'activity_name', title: gettext('Activity'), name: 'activity__name'},
            {data: 'activitygroup_name', title: gettext('Activity Group'), name: 'activity__activitygroup__name'},
            {data: 'city', title: gettext('City'), name: 'administrative_location.city'},
            {data: 'address', title: gettext('Address'), name: 'administrative_location.address'},
        ];
        var table = this.el.querySelector('#actor-select-modal table');

        var url = config.api.actors.format(this.caseStudyId, this.keyflowId);
        this.actorsDatatable = $(table).DataTable({
            serverSide: true,
            ajax: url + "?format=datatables",
            columns: columns,
            rowId: 'id'
        });
        var body = table.querySelector('tbody');
        $(body).on( 'click', 'tr', function () {
            if ( $(this).hasClass('selected') ) {
                $(this).removeClass('selected');
            }
            else {
                _this.actorsDatatable.$('tr.selected').removeClass('selected');
                $(this).addClass('selected');
            }
        } );

        // add individual search fields for all columns
        $(table).append('<tfoot><tr></tr></tfoot>');
        var footer = $('tfoot tr', table);
        var delay = (function(){
            var timer = 0;
            return function(callback, ms){
                clearTimeout (timer);
                timer = setTimeout(callback, ms);
            };
        })();
        this.actorsDatatable.columns().every( function () {
            var column = this;
            if (column.visible()){
                var searchInput = document.createElement('input'),
                    th = document.createElement('th');
                searchInput.placeholder = gettext('Search');
                th.appendChild(searchInput);
                searchInput.name = columns[column.index()].data;
                searchInput.style.width = '100%';
                searchInput.autocomplete = "off";
                footer.append(th);
                $(searchInput).on( 'keyup change', function () {
                    var input = this;
                    if ( column.search() !== input.value ) {
                        delay(function(){
                            column.search(input.value).draw();
                        }, 400 );
                    }
                });
            }
        });
    },

    /*
    * render the edit-view on a node
    */
    renderNodeView: function(node, options){
        var options = options || {},
            model = node.model,
            _this = this;

        function selectActor(onConfirm){
            _this.onConfirmActor = function(id){
                model = new GDSEModel( {id: id}, {
                    apiTag: 'actors',
                    apiIds: [ _this.caseStudyId, _this.keyflowId ]
                });
                node.model = model;
                onConfirm();
                // select "Select Actor" node when confirmed
                $('#data-tree').treeview('selectNode', [_this.selectedNode, { silent: true }]);
            }
            var modal = $('#actor-select-modal'),
                activity = _this.activities.get(node.parentActivityId),
                activityInput = $('input[name="activity_name"]', modal);
            activityInput.val(activity.get('name'));
            activityInput.trigger('change');
            //_this.actorsDatatable.search( activity.get('name') ).draw();
            modal.modal('show');
        }

        function render(){
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
        }

        if (node.tag == 'actorSelect' && !options.rerender){
            // patternfly-bootstrap-treeview bug workaround
           if (this.selectedNode){
                var _node;
                $('#data-tree').treeview('getNodes').forEach(function(node){
                    if (node.nodeId == _this.selectedNode.nodeId) _node = node;
                })

                // select previous node (so that "Select Actor" is not highlighted on cancel)
                $('#data-tree').treeview('selectNode', [_node, { silent: true }]);
            }
            selectActor(render);
        }
        else render();
    },

    confirmActorSelection: function(){
        var selected = this.actorsDatatable.row('.selected');
        this.actorsDatatable.$('tr.selected').removeClass('selected');
        if (!selected) return;
        var data = selected.data();
        this.onConfirmActor(data.id);
    },

});
return FlowsEditView;
});
