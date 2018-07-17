define(['backbone', 'underscore', 'views/study-area/workshop-maps', 
        'collections/gdsecollection', 'models/gdsemodel',
        'visualizations/map', 'app-config'],

function(Backbone, _, BaseMapView, GDSECollection, GDSEModel, Map, config){
/**
*
* @author Christoph Franke
* @name module:views/SetupMapsView
* @augments  module:views/BaseMapView
*/
var SetupMapsView = BaseMapView.extend(
    /** @lends module:views/SetupMapsView.prototype */
    {

    includedOnly: false,
    // check/uncheck node when clicked on row, else only if clicked on checkbox
    rowClickCheck: false,

    initialize: function(options){
        SetupMapsView.__super__.initialize.apply(this, [options]);
        _.bindAll(this, 'repositionButtons');
        _.bindAll(this, 'nodeSelected');
    },

    /*
        * dom events (managed by jquery)
        */
    events: {
        'click #layer-tree-buttons>.add': 'addLayer',
        'click #add-layer-category-button': 'addCategory',
        'click #add-layer-modal .confirm': 'confirmLayer',
        'click #layer-tree-buttons>.remove': 'removeNode',
        'click #layer-tree-buttons>.edit': 'editName',
        'click #refresh-wms-services-button': 'renderAvailableServices',
    },
    
    // determines if a layer is checked on start ('included' layers in setup mode)
    isChecked: function(layer){
        return layer.get('included');
    },

    // setup mode doesn't need to store anything in the session
    // all saved directly in db -> override and leave empty
    saveCheckstates(){
    },
    restoreOrder(){
    },

    /*
    * render the view
    */
    render: function(){
        this.renderTemplate();

        this.buttonBox = document.getElementById('layer-tree-buttons');
        this.zInput = document.getElementById('layer-z-index');

        this.layerModal = document.getElementById('add-layer-modal');


        // preselect first category
        categoryIds = Object.keys(this.categoryTree);
        var preselect = (categoryIds.length > 0) ? categoryIds[0] : null;
        this.renderLayerTree(preselect);

        this.renderAvailableServices();
        this.renderMap();
    },
    
    rerenderTree: function(){
        $(this.layerTree).jstree("destroy");
        this.renderLayerTree();
    },
    
    renderLayerTree: function(){
        SetupMapsView.__super__.renderLayerTree.call(this);
        var _this = this;
        $(this.layerTree).on("open_node.jstree", function(){ _this.buttonBox.style.display='none' });
        $(this.layerTree).on("close_node.jstree", function(){ _this.buttonBox.style.display='none' });
        $(this.layerTree).on("after_open.jstree", this.repositionButtons);
        $(this.layerTree).on("after_close.jstree", this.repositionButtons);
    },

    // place buttons over currently selected node
    repositionButtons(){
        var id = $(this.layerTree).jstree('get_selected')[0],
            li = this.layerTree.querySelector('#' + id);
        if (!li) {
            this.buttonBox.style.display = 'none';
            return;
        }
        this.buttonBox.style.top = li.offsetTop + this.layerTree.offsetTop + 'px';
        this.buttonBox.style.display = 'inline';
    },
    
    nodeDropped: function(event, data){
        var node = data.node,
            parent = $(this.layerTree).jstree("get_node", node.parent),
            siblings = parent.children,
            _this = this;
        var i = 0;
        siblings.forEach(function(sibling){
            var n = $(_this.layerTree).jstree("get_node", sibling),
                model = (n.type === 'category') ? n.original.category : n.original.layer;
            model.set('order', i);
            model.save();
            i++;
        })
        this.setMapZIndices();
    },

    /*
    * event for selecting a node in the layer tree
    */
    nodeSelected: function(event, data){
        var node = data.node,
            addBtn = this.buttonBox.querySelector('.add'),
            removeBtn = this.buttonBox.querySelector('.remove');
        this.selectedNode = node;
        if (node.type === 'layer') {
            addBtn.style.display = 'None';
        }
        else {
            addBtn.style.display = 'inline';
        }
        this.repositionButtons();
    },
    
    applyCheckState: function(node){
        var _this = this;
        function applyLayerCheck(layerNode){
            var isChecked = layerNode.state.checked,
                layer = layerNode.original.layer;
            layer.set('included', isChecked);
            layer.save();
            _this.map.setVisible(_this.layerPrefix + layer.id, isChecked);
            var legendDiv = document.getElementById(_this.legendPrefix + layer.id),
                display = (isChecked) ? 'inline': 'none';
            if (legendDiv) legendDiv.style.display = display;
        }
        if (node.type === 'layer')
            applyLayerCheck(node)
        // cascading checks don't fire check_node event -> update child layers if category is checked
        else {
            node.children.forEach(function(child){ 
                applyLayerCheck($(_this.layerTree).jstree('get_node', child));
            });
        }
    },

    nodeChecked: function(event, data){
        this.applyCheckState(data.node);
    },

    nodeUnchecked: function(event, data){
        this.applyCheckState(data.node);
    },

    renderAvailableServices: function(){
        var _this = this;
        this.wmsResources.fetch({ success: function(){
            var html = document.getElementById('wms-services-template').innerHTML,
                template = _.template(html),
                el = document.getElementById('wms-services');
            el.innerHTML = template({ resources: _this.wmsResources });
        }})
    },

    addLayer: function(){
        // uncheck all checkboxes
        var checked = this.layerModal.querySelectorAll('input[name=layer]:checked');
        checked.forEach(function(checkbox){checkbox.checked = false;})
        $(this.layerModal).modal('show');
    },

    addCategory: function(){
        var _this = this;
        function onConfirm(name){
            var category = _this.layerCategories.create( { name: name }, { 
                success: function(){
                    var catNode = {
                        text: name,
                        category: category,
                        type: 'category',
                        children: []
                    }
                    var treeIsEmpty = Object.keys(_this.categoryTree).length === 0;
                    _this.categoryTree[category.id] = catNode;
                    // bug in jstree: tree is not correctly initiallized when empty
                    if (treeIsEmpty)
                        _this.rerenderTree();
                    else
                        _this.addNode(catNode);
                },
                error: _this.onError,
                wait: true
            });
        }
        this.getName({
            title: gettext('Add Category'),
            onConfirm: onConfirm
        });
    },
    
    addNode: function(node, parentNode){
        var parent = parentNode || null;
        $(this.layerTree).jstree('create_node', parent, node, 'last');
    },

    confirmLayer: function(){
        var _this = this;
        var category = this.selectedNode.original.category,
            catNode = this.categoryTree[category.id],
            checked = this.layerModal.querySelectorAll('input[name=layer]:checked'),
            newLayers = [];
        console.log(catNode)
        checked.forEach(function(checkbox){
            var wmsLayerId = checkbox.dataset.layerid,
                wmsLayerName = checkbox.dataset.layername;
            var layer = new GDSEModel(
                { name: wmsLayerName,
                  included: true,
                  wms_layer: wmsLayerId,
                  style: null }, 
                { apiTag: 'layers', 
                  apiIds: [ _this.caseStudy.id, category.id ] }
            );
            newLayers.push(layer);
        })

        function onSuccess(){
            newLayers.forEach(function(layer){
                var layerNode = { 
                    text: layer.get('name'),
                    layer: layer,
                    type: 'layer',
                    state: { checked: layer.get('included') } 
                };
                catNode.children.push(layerNode);
                _this.addNode(layerNode, _this.selectedNode);
                _this.addServiceLayer(layer);
            })
        }

        // upload the models recursively (starting at index it)
        function uploadModel(models, it){
          // end recursion if no elements are left and call the passed success method
          if (it >= models.length) {
            onSuccess();
            return;
          };
          var params = {
            success: function(){ uploadModel(models, it+1) }
          }
          var model = models[it];
          model.save(null, params);
        };

        // start recursion at index 0
        uploadModel(newLayers, 0);
    },

    removeNode: function(){
        if (!this.selectedNode) return;
        var _this = this;
        var isCategory = (this.selectedNode.type === 'category'),
            model = this.selectedNode.original.chart || this.selectedNode.original.category,
            message = (!isCategory) ? gettext('Do you really want to delete the selected chart?') :
                      gettext('Do you really want to delete the selected category and all its charts?');
        function confirmRemoval(){
            $(_this.confirmationModal).modal('hide'); 
            var model = _this.selectedNode.original.layer || _this.selectedNode.original.category;
            model.destroy({ 
                success: function(){
                    var selectCatId = 0;
                    // remove category from tree (if category was selected)
                    if (isCategory) {
                        _this.selectedNode.children.forEach(function(node){
                            _this.map.removeLayer(_this.layerPrefix + node.original.layer.id);
                        })
                        delete _this.categoryTree[model.id];
                    }
                    // remove chart from category (if chart was selected)
                    else {
                        _this.getTreeLayerNode(model, { pop: true })
                        selectCatId = model.get('category');
                        _this.map.removeLayer(_this.layerPrefix + model.id);
                        var legendDiv = document.getElementById(_this.legendPrefix + model.id);
                        if (legendDiv) legendDiv.parentElement.removeChild(legendDiv);
                    }
                    $(_this.layerTree).jstree("delete_node", _this.selectedNode);
                    _this.buttonBox.style.display = 'None';
                },
                error: _this.onError,
                wait: true
            });
        }
        this.confirm({ message: message, onConfirm: confirmRemoval })
    },

    getTreeLayerNode: function(layer, options){
        var options = options || {},
            catNode = this.categoryTree[layer.get('category')],
            nodes = catNode.children;
        for (var i = 0; i < nodes.length; i++){
            var node = nodes[i];
            if (node.layer === layer) {
                if (options.pop) nodes.splice(i, 1);
                return node;
            }
        }
        return;
    },

    editName: function(){
        var _this = this,
            model = this.selectedNode.original.layer || this.selectedNode.original.category;
        function onConfirm(name){
            model.set('name', name);
            model.save(null, { 
                success: function(){
                    $(_this.layerTree).jstree('set_text', _this.selectedNode, name);
            }})
        };
        this.getName({
            name: model.get('name'),
            title: gettext('Edit Name'),
            onConfirm: onConfirm
        })
    },

});
return SetupMapsView;
}
);
