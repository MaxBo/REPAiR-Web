define(['views/baseview', 'underscore', 'collections/gdsecollection', 
        'models/gdsemodel', 'app-config', 'jstree', 
        'static/css/jstree/gdsetouch/style.css'],

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
        _.bindAll(this, 'repositionButtons');

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
        'click #chart-tree-buttons>.add': 'addChart',
        'click #add-chart-category-button': 'addCategory',
        'click #add-chart-modal .confirm': 'confirmChart',
        'change #chart-image-input': 'showPreview',
        'click #chart-tree-buttons>.remove': 'removeNode',
        'click #chart-tree-buttons>.edit': 'editName'
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
                        chart: chart, 
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
    
    rerenderTree: function(){
        $(this.chartTree).jstree("destroy");
        this.renderChartTree();
    },

    /*
    * render the hierarchic tree of layers
    */
    renderChartTree: function(){
        if (Object.keys(this.categoryTree).length == 0) return;

        var _this = this,
            tree = [];

        _.each(this.categoryTree, function(category){
            category.tag = 'category';
            tree.push(category);
        })

        $(this.chartTree).jstree({
            core : {
                data: tree,
                themes: {
                    name: 'gdsetouch',
                    responsive: true
                },
                check_callback: true,
                multiple: false
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
                    "uncheck_node": false,
                    "icon": "fa fa-images"
                },
                chart: {
                    "valid_children": [],
                    "icon": "fa fa-image"
                }
            },
            plugins: ["wholerow", "ui", "types", "themes"]
        });
        $(this.chartTree).on("select_node.jstree", this.nodeSelected);
        if (this.mode === 1){
            // button position needs to be recalculated when collapsing/expanding
            $(this.chartTree).on("open_node.jstree", function(){ _this.buttonBox.style.display='none' });
            $(this.chartTree).on("close_node.jstree", function(){ _this.buttonBox.style.display='none' });
            $(this.chartTree).on("after_open.jstree", this.repositionButtons);
            $(this.chartTree).on("after_close.jstree", this.repositionButtons);
        }
    },

    nodeSelected: function(event, data){
        var node = data.node,
            addBtn = this.buttonBox.querySelector('.add'),
            removeBtn = this.buttonBox.querySelector('.remove');
        this.selectedNode = node;
        var preview = this.el.querySelector('#chart-view');
        
        if (node.type === 'chart'){
            preview.src = node.original.chart.get('image'); 
            preview.style.display = 'inline';
        }
        else {
            // category selected in setup mode -> no image; keep previous one in workshop mode
            if (this.mode == 1) {
                preview.src = '#';
                preview.style.display = 'none';
            }
            // expand category on single click in workshop mode
            if (this.mode == 0) {
                $(this.chartTree).jstree('toggle_node', node);
            }
        }
        
        if (this.mode == 1) {
            addBtn.style.display = 'inline';
            removeBtn.style.display = 'inline';
            if (node.type === 'chart') {
                addBtn.style.display = 'None';
            }
            this.repositionButtons();
        }
    },
    
    // place buttons over currently selected node
    repositionButtons(){
        var id = $(this.chartTree).jstree('get_selected')[0],
            li = this.chartTree.querySelector('#' + id);
        if (!li) {
            this.buttonBox.style.display = 'none';
            return;
        }
        this.buttonBox.style.top = li.offsetTop + this.chartTree.offsetTop + 'px';
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
                    var catNode = { 
                        text: name, 
                        type: 'category',
                        category: category,
                        children: []
                    };
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

    confirmChart: function(){
        var preview = this.el.querySelector('.preview'),
            category = this.selectedNode.original.category,
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
                        chart: chart,
                        type: 'chart'};
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
        var _this = this;
        var isCategory = (this.selectedNode.type === 'category'),
            model = this.selectedNode.original.chart || this.selectedNode.original.category,
            message = (!isCategory) ? gettext('Do you really want to delete the selected chart?') :
                      gettext('Do you really want to delete the selected category and all its charts?');
        function confirmRemoval(){
            $(_this.confirmationModal).modal('hide'); 
            var model = _this.selectedNode.original.chart || _this.selectedNode.original.category;
            model.destroy({ 
                success: function(){
                    var selectCatId = 0;
                    // remove category from tree (if category was selected)
                    if (isCategory) {
                        delete _this.categoryTree[model.id];
                    }
                    // remove chart from category (if chart was selected)
                    else {
                        _this.getTreeChartNode(model, { pop : true })
                        selectCatId = model.get("chart_category");
                    }
                    $(_this.chartTree).jstree("delete_node", _this.selectedNode);
                    _this.buttonBox.style.display = 'None';
                },
                error: _this.onError,
                wait: true
            });
        }
        this.confirm({ message: message, onConfirm: confirmRemoval })
    },
    
    addNode: function(node, parentNode){
        var parent = parentNode || null;
        $(this.chartTree).jstree('create_node', parent, node, 'last');
    },
    
    getTreeChartNode: function(chart, options){
        var options = options || {};
        var catNode = this.categoryTree[chart.get('chart_category')];
        var nodes = catNode.children;
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
        var model = this.selectedNode.original.chart || this.selectedNode.original.category;
        function onConfirm(name){
            model.set('name', name);
            model.save({ name: name }, { patch: true, 
                success: function(){
                    $(_this.chartTree).jstree('set_text', _this.selectedNode, name);
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