define(['backbone', 'app/visualizations/sankey', 'app/loader'],
function(Backbone, Sankey){

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
  var DataView = Backbone.View.extend({

    /*
      * view-constructor
      */
    initialize: function(options){
      _.bindAll(this, 'render');
      this.template = options.template;
      this.activityGroups = options.activityGroups;
      this.stocks = options.stocks;
      var _this = this;
      var loader = new Loader(this.el);

      $.when(this.collection.fetch(),  this.stocks.fetch()).then(function() {
          loader.remove();
          if (_this.collection.length > 0)
            _this.render();
      });
    },

    events: {
      'click #fullscreen-toggle': 'toggleFullscreen'
    },

    /*
      * render the view
      */
    render: function(){
      var template = document.getElementById(this.template);
      this.el.innerHTML = template.innerHTML;

      this.sankeyData = this.transformData(this.activityGroups,
                                           this.collection,
                                           this.stocks)
      this.renderSankey(this.sankeyData);
    },

    toggleFullscreen: function(){
      this.el.classList.toggle('fullscreen');
      if (this.sankeyData != null){
        this.renderSankey(this.sankeyData);
      }
    },

    /*
      * render a sankey diagram
      */
    renderSankey: function(data){

      var width = this.el.clientWidth;
      // this.el (#data-view) may be hidden at the moment this view is called
      // (is close to body width then, at least wider as the wrapper of the content),
      // in this case take width of first tab instead, because this one is always shown first
      if (width >= document.getElementById('page-content-wrapper').clientWidth)
        width = document.getElementById('data-entry').clientWidth;
      var height = this.el.classList.contains('fullscreen') ?
                   this.el.clientHeight: width / 3;
      var sankey = new Sankey({
        height: height,
        width: width,
        divid: '#sankey',
        title: ''
      })
      sankey.render(data);
    },

    transformData: function(models, modelLinks, stocks){
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
        links.push({
          value: modelLink.get('amount'),
          source: source,
          target: target
        });
      })
      stocks.each(function(stock){
        var id = 'stock-' + stock.id;
        nodes.push({id: id, name: 'Stock'});
        var source = nodeIdxDict[stock.get('origin')];
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
      * remove this view from the DOM
      */
    close: function(){
      this.undelegateEvents(); // remove click events
      this.unbind(); // Unbind all local event bindings
      this.el.innerHTML = ''; // Remove view from DOM
    },

    generateRandomData: function() {
      var dataObject = new Object();

      var mostNodes = 20;
      var mostLinks = 40;
      var numNodes = Math.floor((Math.random()*mostNodes)+1);
      var numLinks = Math.floor((Math.random()*mostLinks)+1);

      // Generate nodes
      dataObject.nodes = new Array();
      for( var n = 0; n < numNodes; n++ ) {
        var node = new Object();
          node.name = "Node-" + n;
        dataObject.nodes[n] = node;
      }

      // Generate links
      dataObject.links = new Array();
      for( var i = 0; i < numLinks; i++ ) {
        var link = new Object();
          link.target = link.source = Math.floor((Math.random()*numNodes));
          while( link.source === link.target ) { link.target = Math.floor((Math.random()*numNodes)); }
          link.value = Math.floor((Math.random() * 100) + 1);

        dataObject.links[i] = link;
      }

      return dataObject;
    }

  });

  return DataView;
}
);