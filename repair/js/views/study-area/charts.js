define(['views/baseview', 'underscore', 'collections/gdsecollection', 
        'models/gdsemodel', 'app-config', 'jstree', 
        'jstree/dist/themes/default/style.min.css'],

function(BaseView, _, GDSECollection, GDSEModel, config){
/**
*
* @author Christoph Franke
* @name module:views/BaseChartsView
* @augments module:views/BaseView
*/
var BaseChartsView = BaseView.extend(
    /** @lends module:views/BaseChartsView.prototype */
    {

    /**
    * render view to add charts to casestudy
    *
    * @param {Object} options
    * @param {HTMLElement} options.el                          element the view will be rendered in
    * @param {string} options.template                         id of the script element containing the underscore template to render this view
    * @param {Number} [options.mode=0]                         workshop (0, default) or setup mode (1)
    * @param {module:models/CaseStudy} options.caseStudy       the casestudy to add layers to
    *
    * @constructs
    * @see http://backbonejs.org/#View
    */
    initialize: function(options){
        BaseChartsView.__super__.initialize.apply(this, [options]);
        var _this = this;
        _.bindAll(this, 'nodeSelected');

        this.caseStudy = options.caseStudy;
        this.mode = options.mode || 0;

        this.categoryTree = {};
        
        this.chartCategories = new GDSECollection([], { 
            apiTag: 'chartCategories',
            apiIds: [ this.caseStudy.id ]
        });

        this.loader.activate();
        this.chartCategories.fetch({ 
            success: function(){
                _this.loader.deactivate();
                _this.initTree();
            },
            error: function(r){
                _this.loader.deactivate();
                _this.onError;
            }
        })
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'click .chart-control.fullscreen-toggle': 'toggleFullscreen',
        'click #add-chart-button': 'addChart',
        'click #add-chart-category-button': 'addCategory',
        'click #add-chart-modal .confirm': 'confirmChart',
        'change #chart-image-input': 'showPreview',
        'click #remove-cc-button': 'removeNode',
        'click #remove-cc-modal .confirm': 'confirmRemoval',
        'click #edit-cc-button': 'editName'
    },

    /*
    * render the view
    */
    render: function(){
        var _this = this;
        var html = document.getElementById(this.template).innerHTML
        var template = _.template(html);
        this.el.innerHTML = template();
        this.chartTree = document.getElementById('chart-tree');
        this.buttonBox = document.getElementById('chart-tree-buttons');
        
        html = document.getElementById('empty-modal-template').innerHTML;
        this.confirmationModal = document.getElementById('remove-cc-modal');
        this.confirmationModal.innerHTML = _.template(html)({ header: gettext('Remove') });
        
        if (this.mode == 0) {
            document.getElementById('add-chart-category-button').style.display = 'none';
        }
        
        this.renderChartTree();
    },
    
    initTree: function(){
        var _this = this;
        var promises = [],
            chartList = [];
        // put nodes for each category into the tree and prepare fetching the layers
        // per category
        this.chartCategories.each(function(category){
            var charts = new GDSECollection([], { 
                apiTag: 'charts',
                apiIds: [ _this.caseStudy.id, category.id ]
            });
            charts.categoryId = category.id;
            var node = { 
                text: category.get('name'), 
                category: category,
                children: [],
                type: "category"
            };
            _this.categoryTree[category.id] = node;
            chartList.push(charts);
            promises.push(charts.fetch());
        });
        // fetch prepared layers and put informations into the tree nodes
        Promise.all(promises).then(function(){
            chartList.forEach(function(charts){
                var catNode = _this.categoryTree[charts.categoryId];
                var children = [];
                charts.each(function(chart){
                    var node = { 
                        //chart: chart, 
                        text: chart.get('name'),
                        type: "chart"
                        } 
                    children.push(node);
                });
                catNode.children = children;
            });
            _this.render();
        })
    },


    rerenderChartTree: function(){
        this.buttonBox.style.display = 'None';
        // error when trying to remove, but not initialized yet, safe to ignore
        $(this.chartTree).treeview('remove');
        this.renderChartTree();
    },

    /*
    * render the hierarchic tree of layers
    */
    renderChartTree: function(){
        if (Object.keys(this.categoryTree).length == 0) return;

        var _this = this;
        var dataDict = {};
        var tree = [];

        _.each(this.categoryTree, function(category){
            category.tag = 'category';
            tree.push(category);
        })

        function hideEdits(event, node){
            if (_this.mode == 1)
                _this.buttonBox.style.display = 'None';
        }
        console.log(tree)
        $(this.chartTree).jstree({
            core : {
                data : tree,
                check_callback: true//function(operation, node, node_parent, node_position, more) {
                    //// operation can be 'create_node', 'rename_node', 'delete_node', 'move_node' or 'copy_node'
                    //// in case of 'rename_node' node_position is filled with the new node name
                    
                    //if (operation === "move_node") {
                        //console.log(node)
                        //console.log(node_parent)
                        //return node_parent.original.type === "Parent"; //only allow dropping inside nodes of type 'Parent'
                    //}
                    //return true;  //allow all other operations
                //}
            },
            types: {
                "#" : {
                  "max_depth": -1,
                  "max_children": -1,
                  "valid_children": ["category"],
                },
                category: {
                    "valid_children": ["chart"],
                    "check_node": false,
                    "uncheck_node": false
                },
                chart: {
                    "valid_children": []
                }
            },
            //"dnd": {
                //check_while_dragging: true
            //},
            plugins: ["dnd", "wholerow", "ui", "types"],
          });

        //$(this.chartTree).treeview({
            //data: tree, showTags: true,
            //selectedColor: (_this.mode == 0) ? 'black' : 'white',
            //selectedBackColor: (_this.mode == 0) ? 'rgba(170, 212, 0, 0.3)' : '#aad400',
            //onhoverColor: (_this.mode == 0) ? null : '#F5F5F5',
            //expandIcon: 'glyphicon glyphicon-triangle-right',
            //collapseIcon: 'glyphicon glyphicon-triangle-bottom',
            //preventUnselect: true,
            //allowReselect: true,
            //onNodeSelected: this.nodeSelected,
            //onNodeCollapsed: hideEdits,
            //onNodeExpanded: hideEdits
            ////showCheckbox: true
        //});
    },

    /*
    * event for selecting a node in the material tree
    */
    nodeSelected: function(event, node){
        // unselect previous node (caused by onNodeUnselected)
        if (this.selectedNode)
            $(this.chartTree).treeview('unselectNode', [this.selectedNode, { silent: true }]);
        var addBtn = document.getElementById('add-chart-button');
        var removeBtn = document.getElementById('remove-cc-button');
        this.selectedNode = node;
        
        var preview = this.el.querySelector('#chart-view');
        
        if (node.chart){
            preview.src = node.chart.get('image'); 
            preview.style.display = 'inline';
        }
        // group selected in setup mode -> no image; keep previous one in workshop mode
        else if (this.mode == 1) {
            preview.src = '#';
            preview.style.display = 'none';
        }
        
        // expand/collapse category on click in workshop mode
        if (this.mode == 0) {
            if (node.category){
                // workaround for patternfly-treeview bug
                var nodes = $(this.chartTree).treeview('getNodes'),
                    _node = null;
                nodes.forEach(function(n){
                    if (node.nodeId == n.nodeId) {
                        _node = n;
                    }
                })
                $(this.chartTree).treeview('toggleNodeExpanded', _node);
            }
            // no buttons in workshop mode -> return before showing
            return;
        }
        
        addBtn.style.display = 'inline';
        removeBtn.style.display = 'inline';
        if (node.chart != null) {
            addBtn.style.display = 'None';
        }
        var li = this.chartTree.querySelector('li[data-nodeid="' + node.nodeId + '"]');
        if (!li) return;
        this.buttonBox.style.top = li.offsetTop + 'px';
        this.buttonBox.style.display = 'inline';
    },

    addChart: function(){
        var modal = document.getElementById('add-chart-modal');
        $(modal).modal('show'); 
    },
    
    addCategory: function(){
        var _this = this;
        function onConfirm(name){
            var category = _this.chartCategories.create( { name: name }, { 
                success: function(){
                    console.log(category)
                    var catNode = { 
                        text: name, 
                        category: category,
                        state: { checked: true }
                    };
                    catNode.nodes = [];
                    _this.categoryTree[category.id] = catNode;
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

    confirmChart: function(){
        var preview = this.el.querySelector('.preview'),
            category = this.selectedNode.category,
            _this = this;
        
        var imgInput = this.el.querySelector('#chart-image-input');
        if (imgInput.files && imgInput.files[0]){
        
            // you have to upload files via form, Backbone.Models (sends data as json) doesn't work here
            var image = imgInput.files[0],
                name = this.el.querySelector('#chart-name').value;
            
            var data = {
                name: name,
                image: image
            }
            var chart = new GDSEModel( {}, { apiTag: 'charts', apiIds: [ _this.caseStudy.id, category.id ] });
            chart.save(data, {
                success: function () {
                    var chartNode = { text: chart.get('name'),
                        icon: 'fa fa-image',
                        chart: chart };
                    var catNode = _this.categoryTree[category.id];
                    if (!catNode.nodes) catNode.nodes = [];
                    catNode.nodes.push(chartNode);
                    _this.addNode(chartNode, _this.selectedNode);
                },
                error: _this.onError
            });
        }
        
        else {
            this.alert('No file selected. Canceling upload...')
        }
    },
    
    showPreview: function(event){
        var input = event.target;
        if (input.files && input.files[0]){
            var reader = new FileReader();
            reader.onload = function (e) {
                document.getElementById('chart-image-preview').src = e.target.result;
            };
            reader.readAsDataURL(input.files[0]);
        }
    },
    
    removeNode: function(){
        if (!this.selectedNode) return;
        var model = this.selectedNode.chart || this.selectedNode.category,
            message = (this.selectedNode.chart) ? gettext('Do you really want to delete the selected chart?') :
                      gettext('Do you really want to delete the selected category and all its charts?');
        this.confirmationModal.querySelector('.modal-body').innerHTML = message; 
        $(this.confirmationModal).modal('show'); 
    },
    
    confirmRemoval: function(){
        var _this = this;
        $(this.confirmationModal).modal('hide'); 
        var is_category = (this.selectedNode.category != null);
        var model = this.selectedNode.chart || this.selectedNode.category;
        model.destroy({ 
            success: function(){
                var selectCatId = 0;
                // remove category from tree (if category was selected)
                if (_this.selectedNode.category) {
                    delete _this.categoryTree[model.id];
                }
                // remove chart from category (if chart was selected)
                else {
                    _this.getTreeChartNode(model, { pop : true })
                    selectCatId = model.get("chart_category");
                }
                $(_this.chartTree).treeview('removeNode', _this.selectedNode);
                _this.buttonBox.style.display = 'None';
            },
            error: _this.onError,
            wait: true
        });
        
    },
    
    addNode: function(node, parentNode){
        // patternfly-bootstrap-treeview bug workaround
        if (parentNode){
            var _node;
            $(this.chartTree).treeview('getNodes').forEach(function(node){
                if (node.nodeId == parentNode.nodeId) _node = node;
            })
            parentNode = _node;
        }
        $(this.chartTree).treeview('addNode', [node, parentNode]);
    },
    
    getTreeChartNode: function(chart, options){
        var options = options || {};
        var catNode = this.categoryTree[chart.get('chart_category')];
        var nodes = catNode.nodes;
        for (var i = 0; i < nodes.length; i++){
            var node = nodes[i];
            if (node.chart === chart) {
                if (options.pop) nodes.splice(i, 1);
                return node;
            }
        }
        return;
    },
    
    editName: function(){
        var _this = this;
        var model = this.selectedNode.chart || this.selectedNode.category;
        function onConfirm(name){
            model.set('name', name);
            model.save({ name: name }, { patch: true, 
                success: function(){
                    var node = _this.selectedNode.category ? _this.categoryTree[model.id]:
                                _this.getTreeChartNode(model);
                    node.text = name;
                    var selectCatId = _this.selectedNode.category? model.id: model.get('chart_category');
                    // patternfly-bootstrap-treeview is bugged as hell, updating nodes doesn't work as expected -> need to rerender
                    _this.rerenderChartTree();
                },
                error: _this.onError
            })
        };
        this.getName({ 
            name: model.get('name'), 
            title: gettext('Edit Name'),
            onConfirm: onConfirm
        })
    },
    
    toggleFullscreen: function(event){
        event.target.parentElement.classList.toggle('fullscreen');
    }

});
return BaseChartsView;
}
);