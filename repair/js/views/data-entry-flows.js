define(['backbone', 'underscore',
        'views/data-entry-edit-node',
        'collections/activities', 'collections/actors', 'collections/flows', 'collections/stocks',
        'collections/activitygroups', 'collections/publications', 
        'visualizations/sankey', 'utils/loader'],
function(Backbone, _, EditNodeView, Activities, Actors, Flows, 
         Stocks, ActivityGroups, Publications, Sankey, Loader){

  /**
   *
   * @author Christoph Franke
   * @name module:views/FlowsView
   * @augments Backbone.View
   */
  var FlowsView = Backbone.View.extend( 
    /** @lends module:views/FlowsView.prototype */
    {

    /**
     * render view to edit flows of a single keyflow
     *
     * @param {Object} options
     * @param {HTMLElement} options.el                          element the view will be rendered in
     * @param {module:collections/Keyflows.Model} options.model the keyflow (defining the type of flows that will be rendered)
     * @param {module:models/CaseStudy} options.caseStudy       the casestudy
     * @param {module:collections/Materials} options.materials  the available materials
     *
     * @constructs
     * @see http://backbonejs.org/#View
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
      this.actors = new Actors([], {caseStudyId: this.caseStudyId, keyflowId: this.keyflowId});
      this.activities = new Activities([], {caseStudyId: this.caseStudyId, keyflowId: this.keyflowId});
      this.publications = new Publications([], { caseStudyId: this.caseStudyId });

      var loader = new Loader(document.getElementById('flows-edit'),
                              {disable: true});

      $.when(this.actors.fetch({data: 'included=True'}, 
             this.activityGroups.fetch(), this.activities.fetch(), 
             this.publications.fetch())).then(function(){
        _this.render();
        loader.remove();
      });
    },
    
    /*
     * dom events (managed by jquery)
     */
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
      this.el.innerHTML = template({casestudy: this.caseStudy.get('properties').name,
                                    keyflow: this.model.get('name')});
      this.renderDataTree();
      this.renderSankey();
    },
    
    
    /*
     * render sankey-diagram in fullscreen
     */
    toggleFullscreen: function(){
      document.getElementById('sankey-wrapper').classList.toggle('fullscreen');
      this.renderSankey({skipFetch: true});
    },

    /*
     * render the sankey diagram
     *
     * @param {boolean} options.skipFetch   if True, don't fetch the models to render again, but use the already fetched ones
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
    
    /*
     * transform the models, their links and the stocks to a json-representation
     * readable by the sankey-diagram
     */
    transformData: function(models, flows, stocks){
      var _this = this;
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
      
      function compositionRepr(composition){
        var text = '';
          if (composition){
            var fractions = composition.fractions;
            fractions.forEach(function(fraction){
              var material = _this.materials.get(fraction.material);
              text += '\n' + fraction.fraction * 100 + '% ';
              text += material.get('name');
            })
          }
        return text || ('\nno composition defined')
      }
      
      flows.each(function(flow){
        var value = flow.get('amount');
        var source = nodeIdxDict[flow.get('origin')];
        var target = nodeIdxDict[flow.get('destination')];
        var composition = flow.get('composition');
        
        links.push({
          value: flow.get('amount'),
          source: source,
          target: target,
          text: compositionRepr(composition)
        });
      })
      stocks.each(function(stock){
        var id = 'stock-' + stock.id;
        var source = nodeIdxDict[stock.get('origin')];
        nodes.push({id: id, name: 'Stock', alignToSource: {x: 80, y: 0}});
        var composition = stock.get('composition');
        links.push({
          value: stock.get('amount'),
          source: source,
          target: i,
          text: compositionRepr(composition)
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
      require('libs/bootstrap-treeview.min');
      $(divid).treeview({data: dataTree, showTags: true,
                         selectedBackColor: '#aad400',
                         onNodeSelected: onClick,
                         expandIcon: 'glyphicon glyphicon-triangle-right',
                         collapseIcon: 'glyphicon glyphicon-triangle-bottom'
                         //showCheckbox: true
                         });
      $(divid).treeview('collapseAll', {silent: true});
    },

    /*
    * render the edit-view on a node
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
          keyflowId: _this.keyflowId,
          keyflowName: _this.model.get('name'),
          caseStudyId: _this.caseStudyId,
          publications: _this.publications,
          onUpload: _this.renderDataEntry // rerender after upload
        });
      }
      renderNode();
    },

    /**
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