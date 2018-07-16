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
    categoryBackColor: 'white',
    categoryColor: 'black',
    categoryExpanded: true,
    selectedBackColor: '#aad400',
    selectedColor: 'white',
    allowReselect: true,
    preventUnselect: false,
    onhoverColor: '#F5F5F5',

    initialize: function(options){
        SetupMapsView.__super__.initialize.apply(this, [options]);
        _.bindAll(this, 'repositionButtons');
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

    saveSession(){
        // setup mode doesn't need to store anything in the session
        // all saved directly in db
    },

    /*
    * render the view
    */
    render: function(){
        this.renderTemplate();

        this.buttonBox = document.getElementById('layer-tree-buttons');
        this.zInput = document.getElementById('layer-z-index');

        this.layerModal = document.getElementById('add-layer-modal');

        this.renderMap();

        // preselect first category
        categoryIds = Object.keys(this.categoryTree);
        var preselect = (categoryIds.length > 0) ? categoryIds[0] : null;
        this.renderLayerTree(preselect);

        this.renderAvailableServices();
    },

    renderMap: function(){
        var _this = this;
        this.map = new Map({
            el: document.getElementById('base-map'),
            renderOSM: false
        });
        var focusarea = this.caseStudy.get('properties').focusarea;

        // add polygon of focusarea to both maps and center on their centroid
        if (focusarea != null){
            this.map.centerOnCoordinates(focusarea.coordinates[0], { projection: this.projection });
        };
        // get all layers and render them
        Object.keys(this.categoryTree).forEach(function(catId){
            var children = _this.categoryTree[catId].children;
            children.forEach(function(node){ _this.addServiceLayer(node.layer) } );
        })
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

    // items are not unselectable
    nodeUnselected: function(event, node){
        //$(this.layerTree).treeview('selectNode',  [node, { silent: true }]);
    },

    // select item on collapsing (workaround for misplaced buttons when collapsing)
    nodeCollapsed: function(event, node){
        $(this.layerTree).treeview('selectNode',  [node, { silent: false }]);
    },
    nodeExpanded: function(event, node){
        $(this.layerTree).treeview('selectNode',  [node, { silent: false }]);
    },

    nodeChecked: function(event, node){
        // layer checked
        if (node.layer != null){
            node.layer.set('included', true);
            node.layer.save();
            this.map.setVisible(this.layerPrefix + node.layer.id, true);
            var legendDiv = document.getElementById(this.legendPrefix + node.layer.id);
            if (legendDiv) legendDiv.style.display = 'inline';
        }
    },

    nodeUnchecked: function(event, node){
        // layer unchecked
        if (node.layer != null){
            node.layer.set('included', false);
            node.layer.save();
            this.map.setVisible(this.layerPrefix + node.layer.id, false);
            var legendDiv = document.getElementById(this.legendPrefix + node.layer.id);
            if (legendDiv) legendDiv.style.display = 'none';
        }
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
                        type: 'category'
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
                    type: 'layer'
                    //state: { checked: layer.get('included') } 
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
        var options = options || {};
        var catNode = this.categoryTree[layer.get('category')];
        var nodes = catNode.children;
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
        var _this = this;
        var model = this.selectedNode.original.layer || this.selectedNode.original.category;
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

    moveLayerUp: function(){
        var _this = this;
        var layer = this.selectedNode.layer;
        var newVal = Number(this.zInput.value) + 1;
        layer.set('z_index', newVal);
        this.buttonBox.style.pointerEvents = 'none';
        layer.save(null, { success: function(){
            _this.buttonBox.style.pointerEvents = 'auto';
            _this.zInput.value = newVal;
            _this.map.setZIndex(_this.layerPrefix + layer.id, newVal);
        }});
    },

    moveLayerDown: function(){
        var _this = this;
        var layer = this.selectedNode.layer;
        var newVal = Number(this.zInput.value) - 1;
        if (newVal > 0){
            this.zInput.value = newVal;
            layer.set('z_index', newVal);
            this.buttonBox.style.pointerEvents = 'none';
            layer.save(null, { success: function(){
                _this.buttonBox.style.pointerEvents = 'auto';
                _this.zInput.value = newVal;
                _this.map.setZIndex(_this.layerPrefix + layer.id, newVal);
            }});
        }
    },
});
return SetupMapsView;
}
);
