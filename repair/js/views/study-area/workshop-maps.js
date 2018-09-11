define(['views/common/baseview', 'backbone', 'underscore',
        'collections/gdsecollection', 'visualizations/map',
        'app-config', 'openlayers', 'jstree',
        'static/css/jstree/gdsetouch/style.css'],

function(BaseView, Backbone, _, GDSECollection, Map, config, ol){
/**
*
* @author Christoph Franke
* @name module:views/BaseMapsView
* @augments module:views/BaseView
*/
var BaseMapsView = BaseView.extend(
    /** @lends module:views/BaseMapsView.prototype */
    {

    // fetch only layers included by user in setup mode (set true for workshop mode)
    includedOnly: true,
    theme: 'gdsetouch-large',

    /**
    * render view on map layers of casestudy
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
        BaseMapsView.__super__.initialize.apply(this, [options]);
        var _this = this;
        // make sure 'this' references to this view when functions are called
        // from different context
        _.bindAll(this, 'nodeChecked');
        _.bindAll(this, 'nodeUnchecked');
        _.bindAll(this, 'nodeDropped');
        _.bindAll(this, 'nodeSelected');

        this.template = options.template;
        this.caseStudy = options.caseStudy;

        this.projection = 'EPSG:4326';

        this.wmsResources = new GDSECollection([], {
            apiTag: 'wmsresources',
            apiIds: [ this.caseStudy.id ]
        });
        this.layerCategories = new GDSECollection([], {
            apiTag: 'layerCategories',
            apiIds: [ this.caseStudy.id ],
            comparator: 'order'
        });

        this.categoryTree = {};
        this.categoryPrefix = 'category-';
        this.layerPrefix = 'service-layer-';
        this.legendPrefix = 'layer-legend-';

        this.loader.activate();
        this.layerCategories.fetch({ success: function(){
            _this.loader.deactivate();
            _this.initTree();
        }})
        this.lastNode = null;
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
    },

    // determines if a layer is checked on start (stored in session for workshop mode)
    isChecked: function(layer){
        var checked = config.session.get('checkedMapLayers');
        if (!checked) return false;
        return checked.includes(layer.id);
    },

    initTree: function(){
        var _this = this;
        var promises = [],
            layerList = [];
        queryParams = (this.includedOnly) ? {included: 'True'} : {};
        // put nodes for each category into the tree and prepare fetching the layers
        // per category
        this.layerCategories.sort();
        this.layerCategories.each(function(category){
            var layers = new GDSECollection([], {
                apiTag: 'layers',
                apiIds: [ _this.caseStudy.id, category.id ],
                comparator: 'order'
            });
            layers.categoryId = category.id;
            var node = {
                id: _this.categoryPrefix + category.id,
                text: category.get('name'),
                category: category,
                type: 'category',
                children: []
            };
            _this.categoryTree[category.id] = node;
            layerList.push(layers);
            promises.push(layers.fetch({ data: queryParams }));
        });
        // fetch prepared layers and put informations into the tree nodes
        Promise.all(promises).then(function(){
            layerList.forEach(function(layers){
                var catNode = _this.categoryTree[layers.categoryId],
                    children = [];
                layers.sort();
                layers.each(function(layer){
                    var node = {
                        id: _this.layerPrefix + layer.id,
                        layer: layer,
                        text: layer.get('name'),
                        type: 'layer',
                        state: { checked: _this.isChecked(layer) }
                    };
                    children.push(node);
                });
                catNode.children = children;
            });
            _this.render();
        })
    },

    // store checked layers in session
    saveCheckstates(){
        var checkedItems = $(this.layerTree).jstree('get_checked', { full: true }),
            checkedIds = [];
        checkedItems.forEach(function(item){
            if(item.type === 'layer')
                checkedIds.push(item.original.layer.id);
        })
        config.session.save({ checkedMapLayers: checkedIds });
    },

    saveOrder: function(){
        var catNodes = $(this.layerTree).jstree('get_json'),
            order = [],
            _this = this;
        catNodes.forEach(function(catNode){
            var layerNodes = [];
            catNode.children.forEach(function(layerNode){
                var layerId = layerNode.id.replace(_this.layerPrefix, '');
                layerNodes.push(layerId);
            })
            var catId = catNode.id.replace(_this.categoryPrefix, '');
            order.push({ category: catId, layers: layerNodes});
        })
        config.session.save({ layerOrder: order });
    },

    // restore order from session
    restoreOrder: function(){
        var order = config.session.get('layerOrder'),
            _this = this;
        if (!order) return;
        order.forEach(function(item){
            var catId = item.category,
                layerIds = item.layers;
                catNodeId = _this.categoryPrefix + catId;
            $(_this.layerTree).jstree('move_node', catNodeId, '#', 'last');
            layerIds.forEach(function(layerId){
                var layerNodeId = _this.layerPrefix + layerId;
                $(_this.layerTree).jstree('move_node', layerNodeId, catNodeId, 'last');
            })
        });
    },

    /*
    * render the view
    */
    render: function(){
        this.renderTemplate();
        this.renderLayerTree();
        this.renderMap();
        if (this.categoryExpanded) $(this.layerTree).treeview('collapseAll', { silent: false });
    },

    renderTemplate: function(){
        var html = document.getElementById(this.template).innerHTML,
            template = _.template(html);
        this.el.innerHTML = template();
        this.layerTree = document.getElementById('layer-tree');
        this.legend = document.getElementById('legend');
    },

    /*
    * render the hierarchic tree of layers, preselect category with given id (or first one)
    */
    renderLayerTree: function(){
        if (Object.keys(this.categoryTree).length == 0) return;

        var _this = this,
            tree = [];
        this.layerCategories.forEach(function(category){
            tree.push(_this.categoryTree[category.id])
        })
        $(this.layerTree).jstree({
            core : {
                data: tree,
                themes: {
                    name: this.theme,
                    responsive: true,
                    //large: true
                },
                check_callback: function(operation, node, node_parent, node_position, more) {
                    // restrict movement of nodes to stay inside same parent
                    if (operation === "move_node") {
                        if (node.parent !== node_parent.id) return false;
                    }
                    // allow all other operations
                    return true;
                },
                multiple: true
            },
            checkbox : {
                "keep_selected_style": false,
                "whole_node": false,
                "tie_selection": false
            },
            types: {
                "#" : {
                  "max_depth": -1,
                  "max_children": -1,
                  "valid_children": ["category"],
                },
                category: {
                    "valid_children": ["layer"],
                    icon: 'far fa-map',
                },
                layer: {
                    "valid_children": [],
                    icon: false
                }
            },
            plugins: ["dnd", "checkbox", "wholerow", "ui", "types", "themes"]
        });
        this.restoreOrder();
        $(this.layerTree).on("select_node.jstree", this.nodeSelected);
        $(this.layerTree).on("check_node.jstree", this.nodeChecked);
        $(this.layerTree).on("uncheck_node.jstree", this.nodeUnchecked);
        $(this.layerTree).on("move_node.jstree", this.nodeDropped);
    },

    nodeSelected: function(event, data){
        var node = data.node;
        console.log(node)
        if (node.type === 'category') $(this.layerTree).jstree('toggle_node', node);
        if (node.type === 'layer'){
            if (node.state.checked) $(this.layerTree).jstree('uncheck_node', node);
            else $(this.layerTree).jstree('check_node', node);
        }
    },

    nodeDropped: function(event, data){
        this.saveOrder();
        this.setMapZIndices();
    },

    applyCheckState: function(node){
        var _this = this;
        function applyLayerCheck(layerNode){
            var isChecked = layerNode.state.checked,
                layer = layerNode.original.layer;

            _this.map.setVisible(_this.layerPrefix + layer.id, isChecked);
            var legendDiv = document.getElementById(_this.legendPrefix + layer.id),
                display = (isChecked) ? 'block': 'none';
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
        this.saveCheckstates();
    },

    nodeChecked: function(event, data){
        this.applyCheckState(data.node);
    },

    nodeUnchecked: function(event, data){
        this.applyCheckState(data.node);
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
            var poly = new ol.geom.Polygon(focusarea.coordinates[0]);
            this.map.centerOnPolygon(poly, { projection: this.projection });
        };
        // get all layers and render them
        Object.keys(this.categoryTree).forEach(function(catId){
            var children = _this.categoryTree[catId].children;
            children.forEach(function(node){ _this.addServiceLayer(node.layer) } );
        })
        this.setMapZIndices();
    },

    setMapZIndices: function(){
        // use get_json to get all nodes in a flat order
        var nodes = $(this.layerTree).jstree('get_json', '#', { flat: true }),
            zIndex = nodes.length,
            _this = this;
        nodes.forEach(function(node){
            if(node.type === 'layer'){
                _this.map.setZIndex(node.id, zIndex);
                zIndex--;
            }
        })
    },

    addServiceLayer: function(layer){
        this.map.addServiceLayer(this.layerPrefix + layer.id, {
            opacity: 1,
            visible: this.isChecked(layer),
            url: config.views.layerproxy.format(layer.id),
            //params: {'layers': layer.get('service_layers')}//, 'TILED': true, 'VERSION': '1.1.0'},
        });
        var uri = layer.get('legend_uri');
        if (uri) {
            var legendDiv = document.createElement('li'),
                head = document.createElement('b'),
                img = document.createElement('img');
            legendDiv.id = this.legendPrefix + layer.id;
            head.innerHTML = layer.get('name');
            img.src = uri;
            var itemsDiv = this.legend.querySelector('.items');
            itemsDiv.appendChild(legendDiv);
            legendDiv.appendChild(head);
            legendDiv.appendChild(document.createElement('br'));
            legendDiv.appendChild(img);
            if (!layer.get('included'))
                legendDiv.style.display = 'none';
        }
    },

});
return BaseMapsView;
}
);
