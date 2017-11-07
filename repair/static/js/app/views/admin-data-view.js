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
      console.log(this.activityGroups);
      var loader = new Loader(this.el);
      
      this.activityGroups.fetch({success: function(){
        _this.collection.fetch({
          success: function(){
            loader.remove();
            _this.render();
        }});
      }});
    },

    /*
     * render the view
     */
    render: function(){
      console.log(this.collection);
      this.renderSankey();
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
    renderSankey: function(){
      function generateRandomData() {
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
      };
      var sankey = new Sankey({
        height: 600,
        divid: '#sankey',
        title: 'D3 Sankey with cycle-support (random data, new data on click on "Refresh"-button)'
      })
      var randomData = generateRandomData();
      sankey.render(randomData);
    }

  });
  return DataView;
}
);