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

    initialize: function(options){
        SetupMapsView.__super__.initialize.apply(this, [options]);
        _.bindAll(this, 'confirmRemoval');
    },

    /*
        * dom events (managed by jquery)
        */
    events: {
        'click #add-layer-button': 'addLayer',
        'click #add-category-button': 'addCategory',
        'click #add-layer-modal .confirm': 'confirmLayer',
        'click #remove-layer-button': 'removeLayer',
        'click #edit-layer-button': 'editName',
        'click #refresh-wms-services-button': 'renderAvailableServices',
        'click #move-layer-up-button': 'moveLayerUp',
        'click #move-layer-down-button': 'moveLayerDown'
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
        this.renderDataTree(preselect);

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
            var children = _this.categoryTree[catId].nodes;
            children.forEach(function(node){ _this.addServiceLayer(node.layer) } );
        })
    },

    rerenderDataTree: function(categoryId){
        this.buttonBox.style.display = 'None';
        if (this.layerTree.innerHTML)
            $(this.layerTree).treeview('remove');
        this.renderDataTree(categoryId);
    },


    /*
    * event for selecting a node in the layer tree
    */
    nodeSelected: function(event, node){
        // unselect previous node (caused by onNodeUnselected)
        if (this.selectedNode)
            $(this.layerTree).treeview('unselectNode', [this.selectedNode.nodeId, { silent: true }]);
        var addBtn = document.getElementById('add-layer-button'),
            removeBtn = document.getElementById('remove-layer-button'),
            downBtn = document.getElementById('move-layer-down-button'),
            upBtn = document.getElementById('move-layer-up-button');
        this.selectedNode = node;
        if (node.layer != null) {
            addBtn.style.display = 'None';
            this.zInput.style.display = 'inline';
            this.zInput.value = node.layer.get('z_index');
            downBtn.style.display = 'inline';
            upBtn.style.display = 'inline';
        }
        else {
            addBtn.style.display = 'inline';
            this.zInput.style.display = 'None';
            downBtn.style.display = 'None';
            upBtn.style.display = 'None';
        }
        var li = this.layerTree.querySelector('li[data-nodeid="' + node.nodeId + '"]');
        if (!li) return;
        this.buttonBox.style.top = li.offsetTop + 'px';
        this.buttonBox.style.display = 'inline';
    },

    // items are not unselectable
    nodeUnselected: function(event, node){
        $(this.layerTree).treeview('selectNode',  [node.nodeId, { silent: true }]);
    },

    // select item on collapsing (workaround for misplaced buttons when collapsing)
    nodeCollapsed: function(event, node){
        $(this.layerTree).treeview('selectNode',  [node.nodeId, { silent: false }]);
    },
    nodeExpanded: function(event, node){
        $(this.layerTree).treeview('selectNode',  [node.nodeId, { silent: false }]);
    },

    nodeChecked: function(event, node){
        // layer checked
        if (node.layer != null){
            node.layer.set('included', true);
            node.layer.save();
            this.map.setVisible(this.layerPrefix + node.layer.id, true);
            var legendDiv = document.getElementById(this.legendPrefix + node.layer.id);
            if (legendDiv) legendDiv.style.display = 'inline';
            //$(this.layerTree).treeview('checkNode', [node.parentId, { silent: true }]);
        }
        // category checked
        else {
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
        // category cant't be unchecked
        else {
            $(this.layerTree).treeview('checkNode', [node.nodeId, { silent: true }]);
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
                        state: { checked: true }
                    }
                    catNode.nodes = [];
                    _this.categoryTree[category.id] = catNode;
                    _this.rerenderDataTree(category.id);
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

    confirmLayer: function(){
        var _this = this;
        var category = this.selectedNode.category,
            catNode = this.categoryTree[category.id];

        var checked = this.layerModal.querySelectorAll('input[name=layer]:checked');

        var newLayers = [];

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
                var layerNode = { text: layer.get('name'),
                    icon: 'fa fa-bookmark',
                    layer: layer,
                    state: { checked: layer.get('included') } };
                catNode.nodes.push(layerNode);
                _this.rerenderDataTree(category.id);
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

    removeLayer: function(){
        if (!this.selectedNode) return;
        var model = this.selectedNode.layer || this.selectedNode.category,
            message = (this.selectedNode.layer) ? gettext('Do you really want to delete the selected layer?') :
                      gettext('Do you really want to delete the selected category?');
        this.confirm({ message: message, onConfirm: this.confirmRemoval });
    },

    confirmRemoval: function(){
        var _this = this;
        $(this.confirmationModal).modal('hide');
        var is_category = (this.selectedNode.category != null);
        var model = this.selectedNode.layer || this.selectedNode.category;
        model.destroy({ 
            success: function(){
                var selectCatId = 0;
                // remove category from tree (if category was selected)
                if (_this.selectedNode.category) {
                    _this.selectedNode.nodes.forEach(function(node){
                        _this.map.removeLayer(_this.layerPrefix + node.layer.id);
                    })
                    delete _this.categoryTree[model.id];
                }
                // remove layer from category (if layer was selected)
                else {
                    _this.getTreeLayerNode(model, { pop: true })
                    selectCatId = model.get('category');
                    _this.map.removeLayer(_this.layerPrefix + model.id);
                    var legendDiv = document.getElementById(_this.legendPrefix + model.id);
                    if (legendDiv) legendDiv.parentElement.removeChild(legendDiv);
                }
                _this.selectedNode = null;
                _this.rerenderDataTree(selectCatId);
            },
            error: _this.onError,
            wait: true
        });

    },

    getTreeLayerNode: function(layer, options){
        var options = options || {};
        var catNode = this.categoryTree[layer.get('category')];
        var nodes = catNode.nodes;
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
        var model = this.selectedNode.layer || this.selectedNode.category;
        function onConfirm(name){
            model.set('name', name);
            model.save(null, { success: function(){
                var node = _this.selectedNode.category ? _this.categoryTree[model.id]:
                            _this.getTreeLayerNode(model);
                node.text = name;
                var selectCatId = _this.selectedNode.category? model.id: model.get('category');
                _this.rerenderDataTree(selectCatId);
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
