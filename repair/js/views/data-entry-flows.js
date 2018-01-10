define(['jquery', 'backbone', 'underscore',
        'views/data-entry-edit-node',
        'collections/activities', 'collections/actors',
        'collections/products', 'collections/flows', 
        'collections/stocks', 'collections/activitygroups', 
        'visualizations/sankey', 'loader', 'libs/bootstrap-treeview.min'],
function($, Backbone, _, EditNodeView, Activities, Actors, Products, Flows, 
         Stocks, ActivityGroups, Sankey, Loader){

  /**
   *
   * @desc    view on edit flows of a single casestudy
   *
   * @param   options.el     html-element the view will be rendered in
   * @param   options.model  backbone-model of the casestudy
   *
   * @return  the EditFlowsView class (for chaining)
   * @see     tabs for data-entry (incl. a tree with available nodes to edit),
   *          sankey-diagram visualising the data and verification of nodes
   */
  var FlowsView = Backbone.View.extend({
    // the id of the script containing the template for this view

    /*
     * view-constructor
     */
    initialize: function(options){
      _.bindAll(this, 'render');
      _.bindAll(this, 'renderDataTree');
      _.bindAll(this, 'renderDataEntry');
      var _this = this;
      this.template = options.template;
      this.keyflowId = this.model.id;
      this.selectedModel = null;
      this.caseStudy = options.caseStudy;

      this.caseStudyId = this.model.get('casestudy');
      this.materials = options.materials;

      // collections of nodes associated to the casestudy
      this.activityGroups = new ActivityGroups([], {caseStudyId: this.caseStudyId, keyflowId: this.keyflowId});
      this.products = new Products([], {caseStudyId: this.caseStudyId, keyflowId: this.keyflowId});
      this.actors = new Actors([], {caseStudyId: this.caseStudyId, keyflowId: this.keyflowId});
      this.activities = new Activities([], {caseStudyId: this.caseStudyId, keyflowId: this.keyflowId});

      var loader = new Loader(document.getElementById('flows-edit'),
                              {disable: true});

      $.when(this.actors.fetch({data: 'included=True'}, this.products.fetch(), 
             this.activityGroups.fetch(), this.activities.fetch(),
             )).then(function(){
        _this.render();
        loader.remove();
      });
    },
    
    events: {
      'click #fullscreen-toggle': 'toggleFullscreen',
      'click #refresh-dataview-btn': 'renderSankey',
      'change #data-view-type-select': 'renderSankey'
    },

    /*
     * render the view
     */
    render: function(){
      if (this.activityGroups.length == 0)
        return;
      var _this = this;
      var html = document.getElementById(this.template).innerHTML
      var template = _.template(html);
      this.el.innerHTML = template({casestudy: this.caseStudy.get('name'),
                                    keyflow: this.model.get('name')});
      this.renderDataTree();
      this.renderSankey();
    },
    
    
    toggleFullscreen: function(){
      document.getElementById('sankey-wrapper').classList.toggle('fullscreen');
      this.renderSankey({skipFetch: true});
    },

    /*
      * render a sankey diagram
      */
    renderSankey: function(options){
      var options = options || {};
      var el = document.getElementById('sankey-wrapper');
      var loader = new Loader(el, {disable: true});
      var _this = this;
      
      var type = document.getElementById('data-view-type-select').value;

      function render(data){
        var width = el.clientWidth;
        // this.el (#data-view) may be hidden at the moment this view is called
        // (is close to body width then, at least wider as the wrapper of the content),
        // in this case take width of first tab instead, because this one is always shown first
        if (width >= document.getElementById('page-content-wrapper').clientWidth)
          width = document.getElementById('data-entry-tab').clientWidth;
        var height = el.classList.contains('fullscreen') ?
                     el.clientHeight: width / 3;
        var sankey = new Sankey({
          height: height,
          width: width,
          divid: '#sankey',
          title: ''
        })
        sankey.render(data);
      };
      
      // skip reloading data and render
      if (this.sankeyData != null & options.skipFetch){
        loader.remove();
        render(this.sankeyData);
      }
      // (re)load and transform data and render
      else{
        this.flows = new Flows([], {caseStudyId: this.caseStudyId,
                                    keyflowId: this.keyflowId,
                                    type: type});
        this.stocks = new Stocks([], {caseStudyId: this.caseStudyId,
                                      keyflowId: this.keyflowId,
                                      type: type});
        var nodes = (type == 'activity') ? _this.activities :
                    (type == 'actor') ? _this.actors :
                    _this.activityGroups;
        $.when(this.stocks.fetch(), this.flows.fetch()).then(function(){
          _this.sankeyData = _this.transformData(nodes, _this.flows, _this.stocks);
          loader.remove();
          render(_this.sankeyData);
        }
        );
      }
    },

    transformData: function(models, modelLinks, stocks){
      var products = this.products;
      var nodes = [];
      var nodeIdxDict = {}
      var i = 0;
      models.each(function(model){
        var id = model.id;
        var name = model.get('name');
        nodes.push({id: id, name: name});
        nodeIdxDict[id] = i;
        i += 1;
      });
      var links = [];
      modelLinks.each(function(modelLink){
        var value = modelLink.get('amount');
        var source = nodeIdxDict[modelLink.get('origin')];
        var target = nodeIdxDict[modelLink.get('destination')];
        var product = products.get(modelLink.get('product'))
        var productName = (product != null) ? product.get('name') : 'undefined';
        links.push({
          value: modelLink.get('amount'),
          source: source,
          target: target,
          text: productName
        });
      })
      stocks.each(function(stock){
        var id = 'stock-' + stock.id;
        var source = nodeIdxDict[stock.get('origin')];
        nodes.push({id: id, name: 'Stock', alignToSource: {x: 80, y: 0}});
        links.push({
          value: stock.get('amount'),
          source: source,
          target: i
        });
        i += 1;
      });
      var transformed = {nodes: nodes, links: links};
      return transformed;
    },

    /*
     * render the tree with nodes associated to the casestudy
     */
    renderDataTree: function(){
      var _this = this;
      var dataDict = {};
      var activityDict = {};

      this.actors.each(function(actor){
        var node = {
          text: actor.get('name'),
          icon: 'glyphicon glyphicon-user',
          model: actor,
          state: {checked: false}
        };
        var activity_id = actor.get('activity');
        if (!(activity_id in activityDict))
          activityDict[activity_id] = [];
        activityDict[activity_id].push(node);
      });

      this.activityGroups.each(function(group){
        var node = {
          text: group.get('code') + ": " + group.get('name'),
          model: group,
          icon: 'fa fa-cubes',
          nodes: [],
          state: {checked: false}
        };
        dataDict[group.id] = node;
      });

      this.activities.each(function(activity){
        var id = activity.get('id');
        var nodes = (id in activityDict) ? activityDict[id]: [];
        var node = {
          text: activity.get('name'),
          model: activity,
          icon: 'fa fa-cube',
          nodes: nodes,
          state: {checked: false}
        };
        dataDict[activity.get('activitygroup')].nodes.push(node)
      });

      var dataTree = [];
      for (key in dataDict){
        dataTree.push(dataDict[key]);
      };

      // render view on node on click in data-tree
      var onClick = function(event, node){
        _this.selectedModel = node.model;
        _this.renderDataEntry();
      };
      var divid = '#data-tree';
      $(divid).treeview({data: dataTree, showTags: true,
                         selectedBackColor: '#aad400',
                         onNodeSelected: onClick,
                         //showCheckbox: true
                         });
      $(divid).treeview('collapseAll', {silent: true});
    },

    /**
    * render the edit-view on a node
    *
    * @param model  backbone-model of the node
    */
    renderDataEntry: function(){
      var model = this.selectedModel;
      if (model == null)
        return
      if (this.editNodeView != null){
        this.editNodeView.close();
      };
      var _this = this;
      
      function renderNode(){
        // currently selected keyflow
        _this.editNodeView = new EditNodeView({
          el: document.getElementById('edit-node'),
          template: 'edit-node-template',
          model: model,
          materials: _this.materials,
          products: _this.products,
          keyflowId: _this.keyflowId,
          keyflowName: _this.model.get('name'),
          caseStudyId: _this.caseStudyId,
          onUpload: _this.renderDataEntry // rerender after upload
        });
      }
      renderNode();
    },

    /*
     * remove this view from the DOM
     */
    close: function(){
      this.undelegateEvents(); // remove click events
      this.unbind(); // Unbind all local event bindings
      this.el.innerHTML = ''; // Remove view from DOM
    },

  });
  return FlowsView;
});