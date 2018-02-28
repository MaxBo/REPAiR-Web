define(['backbone', 'underscore', 'collections/layercategories', 
        'collections/layers', 'models/layer', 'visualizations/map', 
        'utils/loader', 'app-config', 'bootstrap-colorpicker'],

function(Backbone, _, LayerCategories, Layers, Layer, Map, Loader, config){
  /**
   *
   * @author Christoph Franke
   * @name module:views/BaseMapsView
   * @augments Backbone.View
   */
  var BaseMapsView = Backbone.View.extend(
    /** @lends module:views/BaseMapsView.prototype */
    {

    /**
     * render view to add layers to casestudy
     *
     * @param {Object} options
     * @param {HTMLElement} options.el                          element the view will be rendered in
     * @param {string} options.template                         id of the script element containing the underscore template to render this view
     * @param {module:models/CaseStudy} options.caseStudy       the casestudy to add layers to
     *
     * @constructs
     * @see http://backbonejs.org/#View
     */
    initialize: function(options){
      var _this = this;
      _.bindAll(this, 'render');
      _.bindAll(this, 'nodeSelected');
      
      this.template = options.template;
      this.caseStudy = options.caseStudy;
      
      this.projection = 'EPSG:4326'; 
      
      var GeoLayers = Backbone.Collection.extend({ url: config.geoserverApi.layers })
      
      this.geoLayers = new GeoLayers();
      this.layerCategories = new LayerCategories([], { caseStudyId: this.caseStudy.id });
      
      this.categoryTree = {
      }
    
      var loader = new Loader(this.el, {disable: true});
      $.when(this.geoLayers.fetch(), this.layerCategories.fetch()).then(function(){
        loader.remove();
        _this.initTree();
      })
    },
    
    initTree: function(){
      var _this = this;
      var deferred = [],
          layerList = [];
      // put nodes for each category into the tree and prepare fetching the layers
      // per category
      this.layerCategories.each(function(category){
        var layers = new Layers([], { caseStudyId: _this.caseStudy.id, 
                                      layerCategoryId: category.id });
        var node = { text: category.get('name'), category: category };
        _this.categoryTree[category.id] = node;
        layerList.push(layers);
        deferred.push(layers.fetch());
      });
      // fetch prepared layers and put informations into the tree nodes
      $.when.apply($, deferred).then(function(){
        layerList.forEach(function(layers){
          var catNode = _this.categoryTree[layers.layerCategoryId];
          var children = [];
          layers.each(function(layer){
            var node = { layer: layer, text: layer.get('name'), icon: 'fa fa-bookmark' };
            children.push(node);
          });
          catNode.nodes = children;
        });
        _this.render();
      })
    },

    /*
      * dom events (managed by jquery)
      */
    events: {
      'click #add-layer-button': 'addLayer',
      'click #add-category-button': 'addCategory',
      'click #add-layer-modal .confirm': 'confirmLayer'
    },

    /*
      * render the view
      */
    render: function(){
      var _this = this;
      var html = document.getElementById(this.template).innerHTML
      var template = _.template(html);
      this.el.innerHTML = template();
      
      this.layerTree = document.getElementById('layer-tree');
      this.buttonBox = document.getElementById('layer-tree-buttons');
      
      this.renderMap();
      this.renderDataTree();
      this.renderAvailableLayers();
    },
    
    renderMap: function(){
      var _this = this;
      this.map = new Map({
        divid: 'base-map', 
      });
      var focusarea = this.caseStudy.get('properties').focusarea;
      
      this.map.addLayer('background', {
          stroke: '#aad400',
          fill: 'rgba(170, 212, 0, 0.1)',
          strokeWidth: 1,
          zIndex: 0
        },
      );
      // add polygon of focusarea to both maps and center on their centroid
      if (focusarea != null){
        var poly = this.map.addPolygon(focusarea.coordinates[0], { projection: this.projection, layername: 'background', tooltip: gettext('Focus area') });
        this.map.addPolygon(focusarea.coordinates[0], { projection: this.projection, layername: 'background', tooltip: gettext('Focus area') });
        this.centroid = this.map.centerOnPolygon(poly, { projection: this.projection });
        this.map.centerOnPolygon(poly, { projection: this.projection });
      };
      // get all layers and render them
      Object.keys(this.categoryTree).forEach(function(catId){
        var children = _this.categoryTree[catId].nodes;
        children.forEach(function(node){ _this.addServiceLayer(node.layer) } );
      })
    },
    
    rerenderDataTree: function(selectId){
      this.buttonBox.style.display = 'None';
      $(this.layerTree).treeview('remove');
      this.renderDataTree(selectId);
    },
    
    addServiceLayer: function(layer){
      
      this.map.addServiceLayer(layer.get('name'), { 
          opacity: 0.5,
          url: '/geoserver/proxy/' + layer.id + '/wms',
          params: {'layers': layer.get('service_layers'), 'TILED': true}//, 'VERSION': '1.1.0'},
          //projection: 'EPSG:4326'//layer.get('srs') 
      })
    
    },
    
    /*
     * render the hierarchic tree of layers
     */
    renderDataTree: function(selectId){
    
      var _this = this;
      var dataDict = {};
      var tree = [];
      
      _.each(this.categoryTree, function(category){
        tree.push(category)
      })
      
      require('libs/bootstrap-treeview.min');
      $(this.layerTree).treeview({
        data: tree, showTags: true,
        selectedBackColor: '#aad400',
        expandIcon: 'glyphicon glyphicon-triangle-right',
        collapseIcon: 'glyphicon glyphicon-triangle-bottom',
        onNodeSelected: this.nodeSelected,
        showCheckbox: true
      });
      
      $(this.layerTree).treeview('selectNode', 0);
    },
    
    /*
     * event for selecting a node in the material tree
     */
    nodeSelected: function(event, node){
      var addBtn = document.getElementById('add-layer-button');
      var removeBtn = document.getElementById('remove-button');
      this.selectedNode = node;
      addBtn.style.display = 'inline';
      removeBtn.style.display = 'inline';
      if (node.layer != null) {
        addBtn.style.display = 'None';
      }
      var li = this.layerTree.querySelector('li[data-nodeid="' + node.nodeId + '"]');
      if (!li) return;
      this.buttonBox.style.top = li.offsetTop + 'px';
      this.buttonBox.style.display = 'inline';
    },
    
    renderAvailableLayers: function(){
      var _this = this;
      
      //$('#colorpicker').colorpicker().on('changeColor',
        //function(ev) { this.style.backgroundColor = this.value; }
      //);
      //colorpicker.value = '#ffffff';
      var rows = [];
      var table = document.getElementById('available-layers-table');
      
      this.geoLayers.each(function(layer){
        var row = table.getElementsByTagName('tbody')[0].insertRow(-1);
        row.insertCell(-1).innerHTML = '';
        row.insertCell(-1).innerHTML = layer.get('name');
        rows.push(row);
        
        row.style.cursor = 'pointer';
        row.addEventListener('click', function() {
          _.each(rows, function(r){
            r.classList.remove('selected');
          });
          row.classList.add('selected');
          _this.selectedRepairLayer = layer;
        });
      });
      
    },
    
    addLayer: function(){
      var modal = document.getElementById('add-layer-modal');
      $(modal).modal('show'); 
    },
    
    addCategory: function(){
      var _this = this;
      function onConfirm(name){
        var category = new _this.layerCategories.model(
          { name: name }, { caseStudyId: _this.caseStudy.id })
        category.save(null, { success: function(){
          var catNode = { text: name };
          _this.categoryTree[category.id] = catNode;
          _this.rerenderDataTree();
        }})
      }
      this.getName({ 
        title: gettext('Add Category'),
        onConfirm: onConfirm
      });
    },
    
    confirmLayer: function(){
      var _this = this;
      var repairLayer = this.selectedRepairLayer;
      if (!repairLayer) return;
      var category = this.selectedNode.category,
          catNode = this.categoryTree[category.id];
          
      var layer = new Layer({ 
        name: repairLayer.get('name'), 
        is_repair_layer: true, 
        repair_namespace: repairLayer.get('namespace'), 
        service_layers: repairLayer.get('name'),
        url: '-' 
      }, { caseStudyId: this.caseStudy.id, layerCategoryId: category.id });
      layer.save(null, { success: function(){
        var layerNode = { text: layer.get('name'),
                          icon: 'fa fa-bookmark',
                          layer: layer};
        if (!catNode.nodes) catNode.nodes = [];
        catNode.nodes.push(layerNode);
        _this.rerenderDataTree();
        _this.addServiceLayer(layer);
      }})
    },
    
    /*
     * open modal dialog to enter a name
     * options: onConfirm, name, title
     */
    getName: function(options){
      
      var options = options || {};
      
      var div = document.getElementById('edit-category-modal'),
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
  return BaseMapsView;
}
);