define(['jquery', 'backbone',
        'app/views/admin-edit-node',
        'app/collections/activities', 'app/collections/actors',
        'app/collections/qualities', 'treeview', 'app/loader'],
function($, Backbone, EditNodeView, Activities, Actors, Qualities, treeview){

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
  var DataEntryView = Backbone.View.extend({
    // the id of the script containing the template for this view

    /*
     * view-constructor
     */
    initialize: function(options){
      _.bindAll(this, 'render');
      _.bindAll(this, 'renderDataTree');
      var _this = this;
      this.template = options.template;

      var caseStudyId = this.model.id;

      // collections of nodes associated to the casestudy
      this.activityGroups = options.activityGroups;
      this.activities = new Activities({caseStudyId: caseStudyId});
      this.actors = new Actors({caseStudyId: caseStudyId});
      this.qualities = new Qualities();

      this.render();
    },

    /*
     * dom events (managed by jquery)
     */
    events: {},

    /*
     * render the view
     */
    render: function(){
      var _this = this;
      var template = document.getElementById(this.template);
      this.el.innerHTML = template.innerHTML;

      // render the tree conatining all nodes
      // after fetching their data, show loader-symbol while fetching
      var loader = new Loader(document.getElementById('flows-edit'),
                              {disable: true});
      $.when(this.qualities.fetch(), this.activities.fetch(),
             this.actors.fetch()).then(function() {
        _this.renderDataTree();
        loader.remove();
      });

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
          icon: 'glyphicon glyphicon-tasks',
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
          icon: 'glyphicon glyphicon-cog',
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
        _this.renderDataEntry(node.model);
      };
      var divid = '#data-tree';
      $(divid).treeview({data: dataTree, showTags: true,
                         selectedBackColor: '#aad400',
                         onNodeSelected: onClick,
                         showCheckbox: true});
      $(divid).treeview('collapseAll', {silent: true});
    },

    /**
    * render the edit-view on a node
    *
    * @param model  backbone-model of the node
    */
    renderDataEntry: function(model){
      if (this.editNodeView != null){
        this.editNodeView.close();
      };
      // currently selected material
      var flowSelect = document.getElementById('flows-select');
      this.editNodeView = new EditNodeView({
        el: document.getElementById('edit-node'),
        template: 'edit-node-template',
        model: model,
        materialId: flowSelect.value,
        caseStudyId: this.model.id,
        qualities: this.qualities
      });
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
  return DataEntryView;
});