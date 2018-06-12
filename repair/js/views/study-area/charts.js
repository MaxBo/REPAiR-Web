define(['views/baseview', 'underscore', 'collections/gdsecollection', 
        'models/gdsemodel', "app-config"],

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

        this.categoryTree = {}
        
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
                state: { expanded: true },
                backColor: (_this.mode == 0) ? '#aad400' : 'white',
                color: (_this.mode == 0) ? 'white' : 'black'
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
                        chart: chart, 
                        text: chart.get('name'),
                        icon: 'fa fa-image'
                        } 
                    children.push(node);
                });
                catNode.nodes = children;
            });
            _this.render();
        })
    },


    rerenderChartTree: function(categoryId){
        this.buttonBox.style.display = 'None';
        // error when trying to remove, but not initialized yet, safe to ignore
        $(this.chartTree).treeview('remove');
        this.renderChartTree(categoryId);
    },

    /*
    * render the hierarchic tree of layers
    */
    renderChartTree: function(categoryId){
        if (Object.keys(this.categoryTree).length == 0) return;

        var _this = this;
        var dataDict = {};
        var tree = [];

        _.each(this.categoryTree, function(category){
            category.tag = 'category';
            tree.push(category);
        })
        
        // items are not unselectable
        function nodeUnselected(event, node){
            $(_this.chartTree).treeview('selectNode',  [node.nodeId, { silent: true }]);
        }
        // select item on collapsing (workaround for misplaced buttons when collapsing)
        function nodeCollapsed(event, node){
            if (_this.mode == 1)
                $(_this.chartTree).treeview('selectNode',  [node.nodeId, { silent: false }]);
        }
        function nodeExpanded(event, node){
            if (_this.mode == 1)
                $(_this.chartTree).treeview('selectNode',  [node.nodeId, { silent: false }]);
        }

        require('libs/bootstrap-treeview.min');
        $(this.chartTree).treeview({
            data: tree, showTags: true,
            selectedColor: (_this.mode == 0) ? 'black' : 'white',
            selectedBackColor: (_this.mode == 0) ? 'rgba(170, 212, 0, 0.3)' : '#aad400',
            expandIcon: 'glyphicon glyphicon-triangle-right',
            collapseIcon: 'glyphicon glyphicon-triangle-bottom',
            onNodeSelected: this.nodeSelected,
            onNodeUnselected: nodeUnselected,
            onNodeCollapsed: nodeCollapsed,
            onNodeExpanded: nodeExpanded
            //showCheckbox: true
        });
        
        // look for and expand and select node with given category id
        if (categoryId != null){
            // there is no other method to get all nodes or to search for an attribute
            var nodes = $(this.chartTree).treeview('getEnabled');
            _.forEach(nodes, function(node){
                if (node.category && (node.category.id == categoryId)){
                    selectNodeId = node.nodeId; 
                    $(_this.chartTree).treeview('selectNode', selectNodeId);
                    return false;
                }
            })
        }
        else if (this.mode == 1) $(this.chartTree).treeview('selectNode', 0);
    },

    /*
    * event for selecting a node in the material tree
    */
    nodeSelected: function(event, node){
        // unselect previous node (caused by onNodeUnselected)
        if (this.selectedNode)
            $(this.chartTree).treeview('unselectNode', [this.selectedNode.nodeId, { silent: true }]);
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
        
        if (this.mode == 0) {
            if (node.category){
                // unselect node, so that selection is triggered on continued clicking
                $(this.chartTree).treeview('unselectNode',  [node.nodeId, { silent: true }]);
                var f = (node.state.expanded) ? 'collapseNode' : 'expandNode';
                $(this.chartTree).treeview(f,  node.nodeId);
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
                    _this.rerenderChartTree(category.id);
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
                    _this.categoryTree[category.id].nodes.push(chartNode);
                    _this.rerenderChartTree(category.id);
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
                _this.selectedNode = null;
                _this.rerenderChartTree(selectCatId);
            },
            error: _this.onError,
            wait: true
        });
        
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
                    _this.rerenderChartTree(selectCatId);
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