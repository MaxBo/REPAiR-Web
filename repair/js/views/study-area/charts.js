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
      'click #add-chart-modal .confirm': 'confirmChart'
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
        showCheckbox: true
      });
    },
    
    /*
     * event for selecting a node in the material tree
     */
    nodeSelected: function(event, node){
      var addBtn = document.getElementById('add-chart-button');
      var removeBtn = document.getElementById('remove-cc-button');
      this.selectedNode = node;
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
      preview.style.display = 'inline';
      preview.src = "/static/img/Chart_3.PNG";
      var category = this.categoryTree[this.selectedNode.categoryId];
      var chartNode = { text: "Chart_3.PNG" };
      if (!category.nodes) category.nodes = [];
      category.nodes.push(chartNode);
      this.rerenderChartTree();
    }
    
  });
  return BaseChartsView;
}
);