define(['views/common/baseview', 'backbone', 'underscore',
        'collections/gdsecollection', 'visualizations/map',
        'app-config', 'openlayers', 'bootstrap-slider', 'jstree',
        'static/css/jstree/gdsetouch/style.css',
        'bootstrap-slider/dist/css/bootstrap-slider.min.css'],

function(BaseView, Backbone, _, GDSECollection, Map, config, ol, Slider){
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
        _.bindAll(this, 'nodeExpanded');
        _.bindAll(this, 'showFeatureInfo');

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

    saveTransparencies(){
        config.session.save({ layerTransparencies: this.transparencies });
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
        if (this.layerCategories.size() == 0){
            var warning = document.createElement('h3');
            warning.style.margin = '30px';
            warning.innerHTML = gettext('The map is not set up.');
            this.el.innerHTML = warning.outerHTML;
            return;
        }
        this.renderTemplate();
        this.renderLayerTree();
        this.renderMap();
        if (this.categoryExpanded) $(this.layerTree).treeview('collapseAll', { silent: false });

        var popovers = this.el.querySelectorAll('[data-toggle="popover"]');
        $(popovers).popover({ trigger: "focus", container: 'body' });
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
    renderLayerTree: function(setupMode){
        if (Object.keys(this.categoryTree).length == 0) return;

        var _this = this,
            tree = [];
        this.layerCategories.forEach(function(category){
            // don't render empty categories in workshop mode
            if (!setupMode && _this.categoryTree[category.id].children.length === 0) return;
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
        this.transparencies = config.session.get('layerTransparencies') || {};
        $(this.layerTree).on("select_node.jstree", this.nodeSelected);
        $(this.layerTree).on("check_node.jstree", this.nodeChecked);
        $(this.layerTree).on("uncheck_node.jstree", this.nodeUnchecked);
        $(this.layerTree).on("move_node.jstree", this.nodeDropped);
        $(this.layerTree).on("open_node.jstree", this.nodeExpanded);
    },

    nodeSelected: function(event, data){
        var node = data.node;
        if (node.type === 'category') $(this.layerTree).jstree('toggle_node', node);
        if (node.type === 'layer'){
            if (node.state.checked) $(this.layerTree).jstree('uncheck_node', node);
            else $(this.layerTree).jstree('check_node', node);
        }
    },

    nodeDropped: function(event, data){
        var _this = this;
        this.saveOrder();
        this.setMapZIndices();
        var node = data.node;
        var parent = $(this.layerTree).jstree('get_node', node.parent);
        // type is bugged, disappears here
        // if category is dragged, you need to rerender all slides in all cat.
        if (node.children.length > 0) {
            parent.children.forEach(function(childId){
                child = $(_this.layerTree).jstree('get_node', childId);
                _this.renderSliders(child.children);
            })
        }
        else {
            this.renderSliders(parent.children);
        }
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

    nodeExpanded: function(event, data){
        var children = data.node.children;
        this.renderSliders(children);
    },

    renderSliders(layernames){
        var _this = this;
        layernames.forEach(function(layername){
            var li = _this.layerTree.querySelector('#' + layername),
                wrapper = document.createElement('div'),
                input = document.createElement('input');
            if (!li) return;
            wrapper.style.width = '100%';
            wrapper.style.height = '20px';
            li.appendChild(wrapper);
            wrapper.appendChild(input);
            var slider = new Slider(input, {
                min: 0,
                max: 100,
                step: 1,
                handle: 'square',
                value: _this.transparencies[layername] || 0
            });

            slider.on('slide', function(value){
                _this.transparencies[layername] = value;
                var opacity = (100 - value) / 100;
                _this.map.setOpacity(layername, opacity);
            })

            slider.on('slideStop', function(value){
                _this.saveTransparencies();
            })
        })
    },

    renderMap: function(){
        var _this = this;
        this.map = new Map({
            el: document.getElementById('base-map'),
            renderOSM: false
        });
        this.map.map.on('singleclick', this.showFeatureInfo );

        var focusarea = this.caseStudy.get('properties').focusarea;

        // add polygon of focusarea to both maps and center on their centroid
        if (focusarea != null){
            var poly = new ol.geom.MultiPolygon(focusarea.coordinates);
            this.map.centerOnPolygon(poly, { projection: this.projection });
        };
        // get all layers and render them
        Object.keys(this.categoryTree).forEach(function(catId){
            var children = _this.categoryTree[catId].children;
            children.forEach(function(node){ _this.addServiceLayer(node.layer) } );
        })
        this.setMapZIndices();
    },

    // update the z-indices in map to the current order in tree
    setMapZIndices: function(){
        // use get_json to get all nodes in a flat order
        var nodes = $(this.layerTree).jstree('get_json', '#', { flat: true }),
            zIndex = nodes.length,
            _this = this;
        if (!nodes.forEach) return;
        nodes.forEach(function(node){
            if(node.type === 'layer'){
                _this.map.setZIndex(node.id, zIndex);
                zIndex--;
            }
        })
    },

    addServiceLayer: function(layer){
        var layername = this.layerPrefix + layer.id,
            transparency = this.transparencies[layername] || 0;
        this.map.addServiceLayer(layername, {
            opacity: (100-transparency) / 100,
            visible: this.isChecked(layer),
            url: layer.get('proxy_uri'),
            //params: {'layers': layer.get('service_layers')}//, 'TILED': true, 'VERSION': '1.1.0'},
        });
        function arrayBufferToBase64(buffer) {
            var binary = '';
            var bytes = [].slice.call(new Uint8Array(buffer));
            bytes.forEach((b) => binary += String.fromCharCode(b));
            return window.btoa(binary);
        };

        var uri = layer.get('legend_uri'),
            uri_proxy = layer.get('legend_proxy_uri');
        if (uri) {
            var legendDiv = document.createElement('li'),
                head = document.createElement('b'),
                imgWrapper = document.createElement('div'),
                img = document.createElement('img');
            legendDiv.id = this.legendPrefix + layer.id;
            head.innerHTML = layer.get('name');
            var itemsDiv = this.legend.querySelector('.items');
            itemsDiv.appendChild(legendDiv);
            legendDiv.appendChild(head);
            legendDiv.appendChild(document.createElement('br'));
            legendDiv.appendChild(imgWrapper);
            imgWrapper.style.marginBottom = '10px';
            imgWrapper.appendChild(img);
            if (!this.isChecked(layer))
                legendDiv.style.display = 'none';

            function bufferToImg(buffer){
                var base64Flag = 'data:image/jpeg;base64,',
                    imageStr = arrayBufferToBase64(buffer);
                img.src = base64Flag + imageStr;
            }

            function fetchProxy(){
                fetch(uri_proxy).then(function(response){
                    response.arrayBuffer().then(bufferToImg);
                }).catch(function(error){
                    imgWrapper.innerHTML = gettext('legend not found')
                });
            }

            fetch(uri).then(function(response){
                if (response.status == 200)
                    response.arrayBuffer().then(bufferToImg);
                else
                    fetchProxy();
            }).catch(function(error){
                fetchProxy();
            })
        }
    },

    showFeatureInfo: function(evt){
        var _this = this,
            checkedItems = $(this.layerTree).jstree('get_checked', { full: true });
        var tableWrapper = document.createElement('div'),
            promises = [];
        tableWrapper.style.overflow = 'auto';
        checkedItems.forEach(function(item){
            if(item.type === 'layer'){
                var layer = item.original.layer,
                    mapLayer = _this.map.getLayer(_this.layerPrefix + layer.id);
                var url = mapLayer.getSource().getGetFeatureInfoUrl(
                                evt.coordinate, _this.map.view.getResolution(), 'EPSG:3857',
                                {'INFO_FORMAT': 'application/json'}
                            );
                var promise = fetch(url).then(res => res.json()).then(function(response){
                    var feats = response.features;
                    feats.forEach(function(feat){
                        var props = feat.properties,
                            table = document.createElement('table');
                            header = table.createTHead().insertRow(-1),
                            row = table.insertRow(-1);
                        table.classList.add('entry-table', 'bordered');
                        var th = document.createElement("th")
                        th.innerHTML = gettext('Layer');
                        header.appendChild(th);
                        row.insertCell(-1).innerHTML = layer.get('name');
                        Object.keys(feat).forEach(function(key){
                            // ignore properties and geometry
                            if (['properties', 'geometry'].includes(key)) return;
                            th = document.createElement("th")
                            th.innerHTML = key;
                            header.appendChild(th);
                            row.insertCell(-1).innerHTML = feat[key];
                        })
                        tableWrapper.appendChild(table);
                    })
                }).catch(error => console.error('Error:', error));
                promises.push(promise);
            }
        })
        Promise.all(promises).then(function(){
            _this.info(tableWrapper.outerHTML, { el: _this.el.querySelector('.info') });
        })
    }

});
return BaseMapsView;
}
);
