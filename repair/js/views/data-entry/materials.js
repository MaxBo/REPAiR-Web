define(['views/common/baseview', 'underscore', "models/gdsemodel",
        'utils/utils', 'patternfly-bootstrap-treeview',
        'patternfly-bootstrap-treeview/dist/bootstrap-treeview.min.css'],

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

    materialToNode: function(material){
        var node = {
            id: material.id,
            parent: material.get('parent'),
            text: material.get('name'),
            model: material,
            state: { collapsed: true }
        };
        if (material.get('keyflow') == null){
            node.backColor = "#C6C6C6";
            node.text += ' (' + gettext('read only') + ')';
        }
        return node;
    },

    /*
    * render the hierarchic tree of materials
    */
    renderDataTree: function(){

        var _this = this;
        var expandedIds = expandedIds || []

        // collection to list, prepare it to treeify
        var materialList = [];
        this.materials.each(function(material){
            materialList.push(_this.materialToNode(material));
        });

        // root node "Materials"
        var tree = [{
            id: null,
            parent: null,
            nodes: utils.treeify(materialList), // collection as tree
            text: 'Materials',
            state: { collapsed: false }
        }]

        function hideEdits(event, node){
            _this.buttonBox.style.display = 'None';
            // patternfly has problems to get the nodes right, so this does not work unfortunately
            //if (_this.selectedNode){
                //console.log(_this.selectedNode)
                //$(_this.materialTree).treeview('unselectNode', [_this.selectedNode, {silent: true}]);
            //}
        }

        $(this.materialTree).treeview({
            data: tree, showTags: true,
            selectedBackColor: '#aad400',
            expandIcon: 'glyphicon glyphicon-triangle-right',
            collapseIcon: 'glyphicon glyphicon-triangle-bottom',
            onNodeSelected: this.nodeSelected,
            preventUnselect: true,
            allowReselect: true,
            // workaround for misplaced buttons when collapsing parent node -> select the collapsed node
            onNodeCollapsed: hideEdits,
            onNodeExpanded: hideEdits
        });
    },

    /*
    * clear the data tree and render it again
    */
    rerender: function(){
        this.buttonBox.style.display = 'None';
        $(this.materialTree).treeview('remove');
        this.renderDataTree();
    },

    unselectAll: function(){
        var selected = $(this.materialTree).treeview('getSelected');
        selected.forEach(function(node){
            $(this.materialTree).treeview('unselectNode', [node, {silent: true}]);
        });
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
                    _this.addNode(material, node);
                },
                error: _this.onError
            });
        }
        this.getName({
            title: gettext('Add Material'),
            onConfirm: onChange
        });
    },

    addNode: function(material, parentNode){
        // patternfly-bootstrap-treeview bug workaround
        if (parentNode){
            var _node;
            $(this.materialTree).treeview('getNodes').forEach(function(node){
                if (node.nodeId == parentNode.nodeId) _node = node;
            })
            parentNode = _node;
        }
        var node = this.materialToNode(material);
        $(this.materialTree).treeview('addNode', [node, parentNode]);
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
                        $(_this.materialTree).treeview('removeNode', node);
                        _this.buttonBox.style.display = 'None';
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
