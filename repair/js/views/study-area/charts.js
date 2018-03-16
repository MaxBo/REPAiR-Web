define(['backbone', 'underscore', 'utils/loader'],

function(Backbone, _, Loader){
  /**
   *
   * @author Christoph Franke
   * @name module:views/BaseChartsView
   * @augments Backbone.View
   */
  var BaseChartsView = Backbone.View.extend(
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
    },
    
    /*
     * open modal dialog to enter a name
     * options: onConfirm, name, title
     */
    getName: function(options){
      
      var options = options || {};
      
      var div = document.getElementById('edit-chart-category-modal'),
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
  return BaseChartsView;
}
);