define(['backbone', 'underscore', 'visualizations/map', 'utils/loader', 
        'app-config', 'bootstrap-colorpicker'],

function(Backbone, _, Map, Loader, config){
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
      
      this.focusarea = options.focusarea;
      this.projection = 'EPSG:4326'; 
      
      var GeoLayers = Backbone.Collection.extend({ url: config.geoserverApi.layers })
      
      this.geoLayers = new GeoLayers();
      
      this.categoryTree = {
        1: {text: 'Group 1', categoryId: 1}, 
        2: {text: 'Group 2', categoryId: 2}
      }
    
      var loader = new Loader(this.el, {disable: true});
      this.geoLayers.fetch({ success: function(){
        loader.remove();
        _this.render();
      }});
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
    },
    
    rerenderDataTree: function(selectId){
      this.buttonBox.style.display = 'None';
      $(this.layerTree).treeview('remove');
      this.renderDataTree(selectId);
    },
    
    /*
     * render the hierarchic tree of layers
     */
    renderDataTree: function(selectId){
    
      var _this = this;
      var dataDict = {};
      var tree = [];
      
      _.each(this.categoryTree, function(category){
        category.tag = 'category';
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
      this.buttonBox.style.top = li.offsetTop + 10 + 'px';
      this.buttonBox.style.display = 'inline';
    },
    
    renderAvailableLayers: function(){
      var _this = this;
      
      $('#colorpicker').colorpicker().on('changeColor',
        function(ev) { this.style.backgroundColor = this.value; }
      );
      colorpicker.value = '#ffffff';
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
          _this.selectedGeoLayer = layer;
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
        var nextId = Math.max(...Object.keys(_this.categoryTree).map(Number)) + 1;
        var cat = {text: name, categoryId: nextId};
        _this.categoryTree[nextId] = cat;
        _this.rerenderDataTree();
      }
      this.getName({ 
        title: gettext('Add Category'),
        onConfirm: onConfirm
      });
    },
    
    confirmLayer: function(){
      var layer = this.selectedGeoLayer;
      if (!layer) return;
      var category = this.categoryTree[this.selectedNode.categoryId];
      var layerNode = { text: layer.get('name'),
                        layer: layer };
      var color = this.el.querySelector('#colorpicker').value
      console.log(color)
      this.map.addLayer(layer.id, { 
        fill: color,
        stroke: color,
        source: { 
          url: '/geoserver/ows' + '?id=' + layer.id + '&namespace=' + layer.get('namespace') + '&srs=EPSG:4326',
          projection: 'EPSG:4326'//layer.get('srs') 
        } 
      })
      console.log(this.map.layers)
      if (!category.nodes) category.nodes = [];
      category.nodes.push(layerNode);
      this.rerenderDataTree();
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