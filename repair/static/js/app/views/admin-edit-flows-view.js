define(['backbone', 'app/visualizations/sankey', 'app/admin-data-tree', 
  'app/views/admin-edit-node-view'],
function(Backbone, Sankey, DataTree, EditNodeView){
  var EditFlowsView = Backbone.View.extend({
    template:'edit-flows-template',

    events: {
      'click #refresh-view-btn': 'renderSankey',
    },

    initialize: function(){
      _.bindAll(this, 'render');
      this.render();
    },

    render: function(){
      var _this = this;
      var html = document.getElementById(this.template).innerHTML;
      var template = _.template(html);
      this.el.innerHTML = template();
      this.renderSankey();

      var onClick = function(link){
        _this.renderDataEntry(link.tag);
      };
      this.dataTree = new DataTree({divid: '#data-tree', onClick: onClick})
    },

    renderDataEntry: function(tag){
      var template = '';
      if (tag == 'activity') template = 'edit-activities-template';
      else if (tag == 'activity-group') template = 'edit-groups-template';
      else if (tag == 'actor') template = 'edit-actors-template';
      document.getElementById('data-link').click();
      
      if (this.editNodeView != null){
        this.editNodeView.close();
      }
      this.editNodeView = new EditNodeView(
        {el: document.getElementById('data-entry'),
         template: template}
      );
    },

    close: function(){
      this.unbind(); // Unbind all local event bindings
      this.remove(); // Remove view from DOM
    },

  // ToDo: make a view out of this?
    renderSankey: function(){
    // ToDo: fetch real data when models are implemented
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
  return EditFlowsView;
}
);