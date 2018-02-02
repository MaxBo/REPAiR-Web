define(['backbone', 'underscore', "models/material", 'utils/loader'],

function(Backbone, _, Material, Loader){

  /**
   *
   * @author Christoph Franke
   * @name module:views/MaterialsView
   * @augments Backbone.View
   */
  var MaterialsView = Backbone.View.extend(
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
      _.bindAll(this, 'render');
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
    renderDataTree: function(){
    
      var _this = this;
      var dataDict = {};
      
      // list to tree
      function treeify(list) {
        var treeList = [];
        var lookup = {};
        list.forEach(function(item) {
          lookup[item['id']] = item;
        });
        list.forEach(function(item) {
          if (item['parent'] != null) {
            lookupParent = lookup[item['parent']]
            if (!lookupParent['nodes']) lookupParent['nodes'] = [];
            lookupParent['nodes'].push(item);
          } else {
            treeList.push(item);
          }
        });
        return treeList;
      };
    
      // collection to list, prepare it to treeify
      var materialList = [];
      this.materials.each(function(material){
        var mat = { 
          id: material.id, 
          parent: material.get('parent'),
          text: material.get('name'),
          model: material,
          state: { collapsed: true }
        };
        materialList.push(mat);
      });
      
      // root node "Materials"
      var tree = [{
        id: null,
        parent: null,
        nodes: treeify(materialList), // collection as tree
        text: 'Materials',
        state: { collapsed: false }
      }]
      
      require('libs/bootstrap-treeview.min');
      $(this.materialTree).treeview({
        data: tree, showTags: true,
        selectedBackColor: '#aad400',
        expandIcon: 'glyphicon glyphicon-triangle-right',
        collapseIcon: 'glyphicon glyphicon-triangle-bottom',
        onNodeSelected: this.nodeSelected
      });
    },
    
    rerender: function(){
      this.buttonBox.style.display = 'None';
      $(this.materialTree).treeview('remove');
      this.renderDataTree();
    },
    
    /*
     * event for selecting a node in the material tree
     */
    nodeSelected: function(event, node){
      this.selectedNode = node;
      var editBtn = document.getElementById('edit-material-button');
      if (!node.model) editBtn.style.display = 'None'; // nothing to edit (most likely root)
      else editBtn.style.display = 'inline';
      var li = this.materialTree.querySelector('li[data-nodeid="' + node.nodeId + '"]');
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
        var material = new Material(
          { parent: node.id, name: name }, 
          { caseStudyId: _this.caseStudyId, keyflowId: _this.keyflowId }
        );
        material.save({}, { success: function(){
          _this.materials.add(material);
          _this.rerender();
        }});
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
      if (this.selectedNode == null) return;
      
      function onChange(name){
        console.log(name)
      }
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
      
      var elConfirmation = document.getElementById('delete-material-modal'),
          html = document.getElementById('confirmation-template').innerHTML,
          modal = elConfirmation.querySelector('.modal'),
          template = _.template(html);
      elConfirmation.innerHTML = template({ 
        message: gettext("Do you really want to delete the selected material and all of its children from the database?")
      });
      elConfirmation.querySelector('.confirm').addEventListener('click', function(){
        var loader = new Loader(_this.el, { disable: true });
        node.model.destroy( { success: function(){
          // fetch the materials again because all children of this node will be removed in backend
          _this.materials.fetch({ success: function(){
            _this.rerender();
            loader.remove();
          }});
        }});
      });
      $(modal).modal('show'); 
    },
    
    /*
     * open modal dialog to enter a name
     * options: onConfirm, name, title
     */
    getName: function(options){
      
      var options = options || {};
      
      var div = document.getElementById('edit-material-modal'),
          inner = document.getElementById('empty-modal-template').innerHTML;
          template = _.template(inner),
          html = template({ header:  options.title || '' });
      
      div.innerHTML = html;
      var modal = div.querySelector('.modal');
      var body = modal.querySelector('.modal-body');
      
      var row = document.createElement('div');
      row.classList.add('row');
      var label = document.createElement('div');
      label.innerHTML = gettext('Name');
      var input = document.createElement('input');
      input.style.width = '100%';
      input.value = options.name || '';
      body.appendChild(row);
      row.appendChild(label);
      row.appendChild(input);
      
      modal.querySelector('.confirm').addEventListener('click', function(){
        if (options.onConfirm) options.onConfirm(input.value);
        $(modal).modal('hide');
      });
      
      $(modal).modal('show');
    },
    
    /*
     * remove this view from the DOM
     */
    close: function(){
      this.undelegateEvents(); // remove click events
      this.unbind(); // Unbind all local event bindings
      this.el.innerHTML = ''; //empty the DOM element
    },

  });
  return MaterialsView;
}
);