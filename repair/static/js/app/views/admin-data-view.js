define(['jquery', 'backbone', 'app/visualizations/sankey', 'app/loader'],
function($, Backbone, Sankey){

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
      var _this = this;
      this.activityGroups = options.activityGroups;
      var loader = new Loader(this.el);

      this.activityGroups.fetch({success: function(){
        _this.collection.fetch({
          success: function(){
            if (_this.collection.length > 0)
              _this.render();
            loader.remove();
        }});
      }});
    },

    /*
      * render the view
      */
    render: function(){
      //console.log(this.collection);
      var transformed = this.transformData(this.activityGroups, this.collection)

      //var transformed = this.generateRandomData();

      this.renderSankey(transformed);
    },

    transformData: function(models, modelLinks){
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
        var id = modelLink.id;
        var value = modelLink.get('amount');
        var source = nodeIdxDict[modelLink.get('origin')];
        var target = nodeIdxDict[modelLink.get('destination')];
        links.push({
          value: modelLink.get('amount'), 
          source: source, 
          target: target
        });
      })
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

    /*
      * render a sankey diagram (currently of random data)
      *
      * ToDo: fetch real data when models are implemented
      *       make a view out of this?
      */
    renderSankey: function(data){
      var sankey = new Sankey({
        height: 600,
        divid: '#sankey',
        title: 'D3 Sankey with cycle-support (random data, new data on click on "Refresh"-button)'
      })
      console.log(data);
      sankey.render(data);
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