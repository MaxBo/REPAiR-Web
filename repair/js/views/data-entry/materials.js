define(['views/baseview', 'underscore', "models/gdsemodel", 
        'utils/utils', 'libs/bootstrap-treeview.min',
        'static/css/bootstrap-treeview.min.css'],

function(BaseView, _, GDSEModel, utils){

/**
    *
    * @author Christoph Franke
    * @name module:views/MaterialsView
    * @augments module:views/BaseView
    */
var MaterialsView = BaseView.extend(
    /** @lends module:views/MaterialsView.prototype */
    {

    /**
    * render view to edit the materials of a keyflow
    *
    * @param {Object} options
    * @param {HTMLElement} options.el                          element the view will be rendered in
    * @param {string} options.template                         id of the script element containing the underscore template to render this view
    * @param {module:collections/Keyflows.Model} options.model the keyflow the materials belong to
    * @param {module:models/CaseStudy} options.caseStudy       the casestudy the keyflow belongs to
    * @param {module:collections/Materials} options.materials  the materials available in the keyflow
    *
    * @constructs
    * @see http://backbonejs.org/#View
    */
    initialize: function(options){
        MaterialsView.__super__.initialize.apply(this, [options]);
        _.bindAll(this, 'renderDataTree');
        _.bindAll(this, 'nodeSelected');
        var _this = this;

        this.template = options.template;
        this.caseStudy = options.caseStudy;
        this.keyflowId = this.model.id,
        this.caseStudyId = this.caseStudy.id;

        this.materials = options.materials;

        this.render();
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'click #edit-material-button': 'editMaterial',
        'click #add-material-button': 'addMaterial',
        'click #remove-material-button': 'removeMaterial'
    },

    /*
    * render the view
    */
    render: function(){
        var _this = this;
        var html = document.getElementById(this.template).innerHTML
        var template = _.template(html);
        this.el.innerHTML = template({casestudy: this.caseStudy.get('properties').name,
            keyflow: this.model.get('name')});

        this.buttonBox = document.getElementById('material-tree-buttons');
        this.materialTree = document.getElementById('material-tree');
        this.renderDataTree();

    },


    /*
    * render the hierarchic tree of materials
    */
    renderDataTree: function(selectId){

        var _this = this;
        var expandedIds = expandedIds || []

        // collection to list, prepare it to treeify
        var materialList = [];
        this.materials.each(function(material){
            // expand if id is in given array
            var mat = { 
                id: material.id, 
                parent: material.get('parent'),
                text: material.get('name'),
                model: material,
                state: { collapsed: true }
            };
            if (material.get('keyflow') == null){
                mat.backColor = "#C6C6C6";
                mat.text += ' (' + gettext('read only') + ')';
            }
            materialList.push(mat);
        });

        // root node "Materials"
        var tree = [{
            id: null,
            parent: null,
            nodes: utils.treeify(materialList), // collection as tree
            text: 'Materials',
            state: { collapsed: false }
        }]

        function select(event, node){ 
            $(_this.materialTree).treeview('selectNode', node.nodeId);
        }

        $(this.materialTree).treeview({
            data: tree, showTags: true,
            selectedBackColor: '#aad400',
            expandIcon: 'glyphicon glyphicon-triangle-right',
            collapseIcon: 'glyphicon glyphicon-triangle-bottom',
            onNodeSelected: this.nodeSelected,
            // workaround for misplaced buttons when collapsing parent node -> select the collapsed node
            onNodeCollapsed: select,
            onNodeExpanded: select
        });
        // look for and expand and select node with given material id
        if (selectId){
            // there is no other method to get all nodes or to search for an attribute
            var nodes = $(this.materialTree).treeview('getCollapsed');
            var found;
            _.forEach(nodes, function(node){
                if (node.id == selectId){
                    found = node; 
                    return false; // in lodash forEach behaves like "break"
                }
            })
            if (found){
                $(this.materialTree).treeview('revealNode', [ found.nodeId, { levels: 1, silent: true } ]);
                $(this.materialTree).treeview('selectNode', [ found.nodeId ]);
            }
        }
    },

    /*
        * clear the data tree and render it again
        */
    rerender: function(selectId){
        this.buttonBox.style.display = 'None';
        $(this.materialTree).treeview('remove');
        this.renderDataTree(selectId);
    },

    /*
        * event for selecting a node in the material tree
        */
    nodeSelected: function(event, node){
        this.selectedNode = node;
        var editBtn = document.getElementById('edit-material-button');
        var removeBtn = document.getElementById('remove-material-button');
        // root can't be deleted or edited (root has no model)
        if (!node.model) {
            editBtn.style.display = 'None'; 
            removeBtn.style.display = 'None'; 
        }
        else {
            editBtn.style.display = 'inline';
            removeBtn.style.display = 'inline'; 
        }
        var li = this.materialTree.querySelector('li[data-nodeid="' + node.nodeId + '"]');
        if (!li) return;
        this.buttonBox.style.top = li.offsetTop + 10 + 'px';
        this.buttonBox.style.display = 'inline';
    },

    /*
    * add a material to the tree with selected node as parent
    */
    addMaterial: function(){
        var node = this.selectedNode;
        if (node == null) return;
        var _this = this;

        function onChange(name){
            var material = new GDSEModel( 
                { parent: node.id, name: name }, 
                { apiTag: 'materials', apiIds:[ _this.caseStudyId, _this.keyflowId ] }
            );
            material.save({}, { 
                success: function(){
                    _this.materials.add(material);
                    _this.rerender(material.id);
                },
                error: _this.onError
            });
        }
        this.getName({ 
            title: gettext('Add Material'),
            onConfirm: onChange
        });
    },

    /*
    * edit the selected material 
    */
    editMaterial: function(){
        var node = this.selectedNode;
        if (node == null) return;
        if (this.selectedNode == null) return;

        var _this = this;

        function onChange(name){
            node.model.set('name', name);
            node.model.caseStudyId = _this.caseStudyId;
            node.model.keyflowId = _this.keyflowId;
            node.model.save(null, { 
                success: function(){
                    _this.rerender(node.id);
                },
                error: _this.onError
            });
        };
        this.getName({ 
            name: this.selectedNode.model.get('name'), 
            title: gettext('Edit Material'),
            onConfirm: onChange
        });
    },

    /*
    * remove the selected material 
    */
    removeMaterial: function(){
        var node = this.selectedNode;
        if (node == null) return;
        var _this = this;
        function destroy(){
            node.model.destroy( { success: function(){
                // fetch the materials again because all children of this node will be removed in backend
                _this.loader.activate();
                _this.materials.fetch({ 
                    success: function(){
                        _this.rerender();
                        _this.loader.deactivate();
                    },
                    error: function(response){
                        _this.onError(response);
                        _this.loader.deactivate();
                    }
                });
            }, error: _this.onError});
        }

        var message = gettext("Do you really want to delete the selected material and all of its children from the database?");
        _this.confirm({ 
            message: message,
            onConfirm: destroy
        })

    },
});
return MaterialsView;
}
);