define(['views/common/baseview', 'underscore',
        'views/data-entry/edit-node',
        'views/data-entry/edit-actor',
        'views/common/filter-flows',
        'collections/gdsecollection', 'models/gdsemodel',
        'app-config', 'datatables.net-bs',
        'datatables.net-bs/css/dataTables.bootstrap.css',
        'datatables.net-buttons-bs/css/buttons.bootstrap.min.css','jstree',
        'static/css/jstree/gdsetouch/style.css'
        ],
function(BaseView, _, EditFlowsView, EditActorView, FlowsView, GDSECollection,
    GDSEModel, config){

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
        _.bindAll(this, 'renderFlowsView');
        _.bindAll(this, 'nodeSelected');
        _.bindAll(this, 'removeActor');
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
        this.actors = new GDSECollection([], {
            apiTag: 'actors',
            apiIds: [ this.caseStudyId , this.keyflowId ]
        });
        this.areaLevels = new GDSECollection([], {
            apiTag: 'arealevels',
            apiIds: [ this.caseStudyId  ],
            comparator: 'level'
        });
        this.reasons = new GDSECollection([], {
            apiTag: 'reasons'
        });
        this.showAll = true;

        this.loader.activate();

        var promises = [
            this.activityGroups.fetch(),
            this.publications.fetch(),
            this.areaLevels.fetch(),
            this.reasons.fetch()
        ]
        Promise.all(promises).then(function(){
            _this.areaLevels.sort();
            _this.loader.deactivate();
            _this.render();
        });
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'click #remove-actor-button': 'showRemoveModal',
        'click #add-actor-button': 'addActorEvent',
        'change #included-filter-select': 'changeFilter',
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
        this.el.innerHTML = template({
            casestudy: this.caseStudy.get('properties').name,
            keyflow: this.model.get('name')
        });
        this.el.querySelector('#actors-col').style.display = 'none';
        this.el.querySelector('#edit-col').style.display = 'none';
        this.el.querySelector('#select-actors-tip').style.display = 'none';
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
                icon: 'fa fa-cubes',
                children: [],
                type: 'activitygroup'
            };
            dataDict[group.id] = node;
        });

        this.activities.each(function(activity){
            var id = activity.get('id');
            var node = {
                text: activity.get('name'),
                model: activity,
                type: 'activity'
            };
            dataDict[activity.get('activitygroup')].children.push(node)
        });

        var dataTree = [];
        for (key in dataDict){
            dataTree.push(dataDict[key]);
        };

        this.dataTree = this.el.querySelector('#data-tree');
        $(this.dataTree).jstree({
            core : {
                data: dataTree,
                themes: {
                    name: 'gdsetouch',
                    responsive: true
                },
                check_callback: true,
                multiple: false
            },
            types: {
                "#" : {
                  "max_depth": -1,
                  "max_children": -1,
                  "valid_children": ["activitygroup"],
                },
                activitygroup: {
                    "check_node": false,
                    "uncheck_node": false,
                    "icon": "fa fa-cubes"
                },
                activity: {
                    "valid_children": [],
                    "icon": "fa fa-cube"
                }
            },
            plugins: ["wholerow", "ui", "types", "themes"]
        });
        $(this.dataTree).on("select_node.jstree", this.nodeSelected);
        this.filterSelect = this.el.querySelector('#included-filter-select');
        this.actorsTable = $('#actors-table').DataTable();
        $('#actors-table tbody').on('click', 'tr', function () {
            _this.selectRow(this);
        });
    },

    nodeSelected: function(event, data){
        var node = data.node;
        if (node.type === 'activitygroup')
            $(this.dataTree).jstree('toggle_node', node);
        else
            this.renderActors(node.original.model);
    },

    /*
    * render the edit-view on a node
    */
    renderFlowsView: function(actor){
        var model = actor,
            _this = this;
        if (_this.editFlowsView != null) _this.editFlowsView.close();
        model.caseStudyId = _this.caseStudyId;
        model.keyflowId = _this.keyflowId;
        model.fetch({
            success: function(){
                // currently selected keyflow
                _this.editFlowsView = new EditFlowsView({
                    el: document.getElementById('edit-actor-flows'),
                    template: 'edit-node-template',
                    model: model,
                    materials: _this.materials,
                    keyflowId: _this.keyflowId,
                    caseStudyId: _this.caseStudyId,
                    publications: _this.publications,
                    apiTag: 'actors',
                    showNodeInfo: false,
                    onUpload: function() { _this.renderNodeView(model) } // rerender after upload
                });
            }, error: _this.onError
        })
    },

    renderActors: function(activity){
        this.el.querySelector('#select-activities-tip').style.display = 'none';
        this.el.querySelector('#select-actors-tip').style.display = 'block';
        this.el.querySelector('#edit-col').style.display = 'none';
        this.el.querySelector('#actors-col').style.display = 'block';
        var _this = this,
            activityId = activity.id;
            data = (activityId =="-1") ? {} : { activity: activityId }
        this.actorsTable.clear().draw();
        this.loader.activate();
        this.actors.fetch({
            data: data,
            success: function(){
                _this.addActorRows(_this.actors);
                _this.loader.deactivate();
            },
            error: function(e){
                _this.loader.deactivate();
                _this.onError(e);
            }
        });
    },

    changeFilter: function(event){
        var _this = this;
        this.showAll = event.target.value == '0';
        if (!this.showAll){
            $.fn.dataTable.ext.search.push(
                function(settings, data, dataIndex) {
                    return $(_this.actorsTable.row(dataIndex).node()).attr('data-included') == 'true';
                  }
              );
        }
        else $.fn.dataTable.ext.search.pop();
        this.actorsTable.draw();
    },

    addActorRows: function(actors){
        var _this = this,
            dataRows = [];
        actors.forEach(function(actor){
            row = [
                actor.get('name'),
                actor.get('city'),
                actor.get('address'),
                actor.id
            ];
            var dataRow = _this.actorsTable.row.add(row);
            dataRows.push(dataRow);
            _this.setIncluded(actor, dataRow);
        });
        this.actorsTable.draw();
        return dataRows;
    },

    showActor: function(actor, dataRow){
        this.el.querySelector('#edit-col').style.display = 'block';
        this.el.querySelector('#select-actors-tip').style.display = 'none';
        var _this = this;
        actor.caseStudyId = _this.caseStudy.id;
        actor.keyflowId = _this.model.id;
        _this.activeActor = actor;
        if (_this.actorView != null) _this.actorView.close();
        actor.fetch({ success: function(){
            _this.actorView = new EditActorView({
                el: _this.el.querySelector('#edit-actor'),
                template: 'edit-actor-template',
                model: actor,
                activities: _this.activities,
                keyflow: _this.model,
                onUpload: function(a) {
                    _this.setIncluded(a, dataRow);
                    dataRow.data([
                        actor.get('name'),
                        actor.get('city'),
                        actor.get('address')
                    ]);
                    _this.showActor(a, dataRow);
                },
                focusarea: _this.caseStudy.get('properties').focusarea,
                areaLevels: _this.areaLevels,
                reasons: _this.reasons
            });
        }})
    },

    selectRow: function(row){
        var _this = this,
            dataRow = this.actorsTable.row(row);
        $("#actors-table tbody tr").removeClass('selected');
        row.classList.add('selected');

        var data = dataRow.data(),
            actor = this.actors.get(data[data.length - 1]);
        this.showActor(actor, dataRow);
        this.renderFlowsView(actor)
    },

    setIncluded: function(actor, dataRow){
        var _this = this,
            included = actor.get('included'),
            row = dataRow.node();
        if (!included){
            row.classList.add('dsbld');
            if (!_this.showAll)
                row.style.display = "none";
        } else {
            row.classList.remove('dsbld')
            row.style.display = "table-row";
        }
        row.setAttribute('data-included', included);
    },

    /*
    * add row on button click
    */
    addActorEvent: function(event){
        var _this = this;
        var buttonId = event.currentTarget.id;
        var tableId;

        function onChange(name){
            var actor = _this.actors.create({
                "BvDid": "-",
                "name": name || "-----",
                "consCode": "-",
                "year": null,
                "turnover": null,
                "employees": null,
                "BvDii": "-",
                "website": "www.website.org",
                "activity": _this.activities.first().id,
                'reason': null,
                'description': ''
            }, {
                wait: true,
                success: function(){
                    var dataRow = _this.addActorRows([actor])[0];
                    _this.selectRow(dataRow.node());
                }
            })
        }
        this.getName({
            title: gettext('Add Actor'),
            onConfirm: onChange
        });
    },

    /*
    * show modal for removal on button click
    */
    showRemoveModal: function(){
        if (this.activeActor == null) return;
        var message = gettext('Do you really want to delete the actor') + ' &#60;' + this.activeActor.get('name') + '&#62; ' + '?';
        this.confirm({ message: message, onConfirm: this.removeActor });
    },

    /*
    * remove selected actor on button click in modal
    */
    removeActor: function(){
        var _this = this;
        this.activeActor.destroy({
            success: function(){
                _this.actorView.close();
                _this.editFlowsView.close();
                _this.activeActor = null;
                _this.actorsTable.row('.selected').remove().draw( false );
            },
            error: _this.onError
        });
    }

});
return FlowsEditView;
});
