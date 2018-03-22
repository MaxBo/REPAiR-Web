define(['views/baseview', 'underscore', 'utils/loader'],

function(BaseView, _, Loader){
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
        var _this = this;
        _.bindAll(this, 'render');
        _.bindAll(this, 'nodeSelected');

        this.template = options.template;
        this.caseStudy = options.caseStudy;
        this.mode = options.mode || 0;

        this.categoryTree = {
            1: {text: 'Group 1', categoryId: 1}, 
            2: {text: 'Group 2', categoryId: 2}
        }

        this.render();
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'click #add-chart-button': 'addChart',
        'click #add-chart-category-button': 'addCategory',
        'click #add-chart-modal .confirm': 'confirmChart',
        'change #chart-image-input': 'showPreview'
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

        if (this.mode == 0) {
            document.getElementById('add-chart-category-button').style.display = 'none';
        }


        this.renderChartTree();
    },


    rerenderChartTree: function(selectId){
        this.buttonBox.style.display = 'None';
        $(this.chartTree).treeview('remove');
        this.renderChartTree(selectId);
    },

    /*
    * render the hierarchic tree of layers
    */
    renderChartTree: function(selectId){

        var _this = this;
        var dataDict = {};
        var tree = [];

        _.each(this.categoryTree, function(category){
            category.tag = 'category';
            tree.push(category);
        })

        require('libs/bootstrap-treeview.min');
        $(this.chartTree).treeview({
            data: tree, showTags: true,
            selectedBackColor: '#aad400',
            expandIcon: 'glyphicon glyphicon-triangle-right',
            collapseIcon: 'glyphicon glyphicon-triangle-bottom',
            onNodeSelected: this.nodeSelected,
            //showCheckbox: true
        });
    },

    /*
    * event for selecting a node in the material tree
    */
    nodeSelected: function(event, node){
        var addBtn = document.getElementById('add-chart-button');
        var removeBtn = document.getElementById('remove-cc-button');
        this.selectedNode = node;

        if (this.mode == 0) return;
        
        addBtn.style.display = 'inline';
        removeBtn.style.display = 'inline';
        if (node.layer != null) {
            addBtn.style.display = 'None';
        }
        var li = this.chartTree.querySelector('li[data-nodeid="' + node.nodeId + '"]');
        if (!li) return;
        this.buttonBox.style.top = li.offsetTop + 10 + 'px';
        this.buttonBox.style.display = 'inline';
    },

    addChart: function(){
        var modal = document.getElementById('add-chart-modal');
        $(modal).modal('show'); 
    },

    addCategory: function(){
        var _this = this;
        function onConfirm(name){
            var nextId = Math.max(...Object.keys(_this.categoryTree).map(Number)) + 1;
            var cat = {text: name, categoryId: nextId};
            _this.categoryTree[nextId] = cat;
            _this.rerenderChartTree();
        }
        this.getName({ 
            title: gettext('Add Category'),
            onConfirm: onConfirm
        });
    },

    confirmChart: function(){
        var preview = this.el.querySelector('.preview');
        //this.el.querySelector('#chart-image-form').submit()
        var input = this.el.querySelector('#chart-image-input');
        if (input.files && input.files[0]){
            var formData = new FormData(),
                image = input.files[0];
            formData.append('image', image, image.name);
            // i didn't want to use AJAX when i don't have to
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/upload', true);
            xhr.onload = function () {
            if (xhr.status === 200) {
                uploadButton.innerHTML = 'Upload';
              } else {
                alert('An error occurred!');
              }
            };
            xhr.send(formData);
        }
        
        
        preview.style.display = 'inline';
        preview.src = "/static/img/Chart_3.PNG";
        var category = this.categoryTree[this.selectedNode.categoryId];
        var chartNode = { text: "Chart_3.PNG" };
        if (!category.nodes) category.nodes = [];
        category.nodes.push(chartNode);
        this.rerenderChartTree();
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
    }

});
return BaseChartsView;
}
);