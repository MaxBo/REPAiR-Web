define(['jquery', 'backbone', 'app/visualizations/sankey',
  'app/views/admin-edit-node-view', 'app/collections/activitygroups', 
  'app/collections/activities', 'app/collections/actors', 
  'app/models/activitygroup', 'app/models/activity', 'app/models/actor',
  'treeview'],
function($, Backbone, Sankey, EditNodeView, ActivityGroups,
         Activities, Actors, ActivityGroup, Activity, Actor, treeview){
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
      
      this.activityGroups.fetch().then(function(){
        _this.activities.fetch().then(function(){
          console.log('actor fetch');
          _this.actors.fetch().then(_this.renderDataTree);
        });
      });
      
    },
    
    renderDataTree: function(){
      var _this = this;
      //console.log(this.activityGroups);
      var dataDict = {};
      var activityDict = {};
      
      console.log(this.actors);
      
      this.actors.each(function(actor){
        var node = {
          text: actor.get('name'),
          icon: 'glyphicon glyphicon-user',
          model: actor
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
      var template = '';
      if (model.constructor === Activity) 
        template = 'edit-activities-template';
      else if (model.constructor === ActivityGroup) 
        template = 'edit-groups-template';
      else if (model.constructor === Actor) 
        template = 'edit-actors-template';
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