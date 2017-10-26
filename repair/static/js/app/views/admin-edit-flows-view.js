define(['jquery', 'backbone', 'app/visualizations/sankey',
  'app/views/admin-edit-node-view', 'app/collections/activitygroups', 
  'app/collections/activities', 'app/collections/actors', 
  'treeview', 'app/loader'],
function($, Backbone, Sankey, EditNodeView, ActivityGroups,
         Activities, Actors, treeview){
  var EditFlowsView = Backbone.View.extend({
    template:'edit-flows-template',

    events: {
      'click #refresh-view-btn': 'renderSankey',
    },

    initialize: function(){
      _.bindAll(this, 'render');
      _.bindAll(this, 'renderDataTree');
      
      var caseStudyId = this.model.id;
      this.activityGroups = new ActivityGroups({caseStudyId: caseStudyId});
      this.activities = new Activities({caseStudyId: caseStudyId});
      this.actors = new Actors({caseStudyId: caseStudyId});

      this.model.fetch({success: this.render});
    },

    render: function(){
      var _this = this;
      var html = document.getElementById(this.template).innerHTML;
      var template = _.template(html);
      this.el.innerHTML = template();
      this.renderSankey();
      
      var loader = Loader(_this.el.querySelector('#data-entry-tab'));
      this.activityGroups.fetch().then(function(){
        _this.activities.fetch().then(function(){
          _this.actors.fetch().then(function(){
            _this.renderDataTree();
            loader.remove();
          });
        });
      });
      
    },
    
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
        var activity_nace = actor.get('own_activity');
        if (!(activity_nace in activityDict))
          activityDict[activity_nace] = [];
        activityDict[activity_nace].push(node);
      });
      
      this.activityGroups.each(function(group){
        var node = {
          text: group.get('code') + ": " + group.get('name'),
          model: group,
          icon: 'glyphicon glyphicon-tasks',
          nodes: []
        };
        dataDict[group.get('code')] = node;
      });
      
      this.activities.each(function(activity){
        var nace = activity.get('nace');
        var nodes = (nace in activityDict) ? activityDict[nace]: [];
        var node = {
          text: activity.get('name'),
          model: activity,
          icon: 'glyphicon glyphicon-cog',
          nodes: nodes
        };
        dataDict[activity.get('own_activitygroup')].nodes.push(node)
      });
      
      var dataTree = [];
      for (key in dataDict){
        dataTree.push(dataDict[key]);
      };
      
      var onClick = function(event, node){
        _this.renderDataEntry(node.model);
      };
      var divid = '#data-tree';
      $(divid).treeview({data: dataTree, showTags: true, 
                         selectedBackColor: '#aad400',
                         onNodeSelected: onClick});
      $(divid).treeview('collapseAll', {silent: true});
    },

    renderDataEntry: function(model){
      if (this.editNodeView != null){
        this.editNodeView.close();
      };
      flowSelect = document.getElementById('flows-select');
      this.editNodeView = new EditNodeView({
        el: document.getElementById('data-entry'),
        template: 'edit-node-template',
        model: model,
        material: flowSelect.value
      });
    },

    close: function(){
      this.unbind(); // Unbind all local event bindings
      this.el.innerHTML = ''; // Remove view from DOM
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