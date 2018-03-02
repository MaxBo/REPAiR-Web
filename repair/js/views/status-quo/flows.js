define(['backbone', 'underscore', 'visualizations/sankey-map',
        'collections/keyflows', 'collections/materials', 
        'collections/actors', 'collections/activitygroups',
        'collections/activities', 'views/flowsankey', 'utils/loader',
        'hierarchy-select'],

function(Backbone, _, SankeyMap, Keyflows, Materials, Actors, ActivityGroups, 
         Activities, FlowSankeyView, Loader){
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
     * render view to show keyflows in casestudy
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
      _.bindAll(this, 'keyflowChanged');
      _.bindAll(this, 'refreshMap');
      
      this.template = options.template;
      this.caseStudy = options.caseStudy;
      this.filter_params = null;
      
      this.keyflows = new Keyflows([], { caseStudyId: this.caseStudy.id });
      
      this.keyflows.fetch({ success: function(){
        _this.render();
      }})
    },

    /*
     * dom events (managed by jquery)
     */
    events: {
      'change select[name="keyflow"]': 'keyflowChanged',
      'click a[href="#flow-map-panel"]': 'refreshMap',
      'change #data-view-type-select': 'renderSankey'
    },

    /*
     * render the view
     */
    render: function(){
      var _this = this;
      var html = document.getElementById(this.template).innerHTML
      var template = _.template(html);
      this.el.innerHTML = template({ keyflows: this.keyflows });
    },
    
    refreshMap: function(){
      if (this.sankeyMap) this.sankeyMap.refresh();
    },
    
    keyflowChanged: function(evt){
      var _this = this;
      this.keyflowId = evt.target.value;
      this.renderSankeyMap();
      var content = this.el.querySelector('#flows-setup-content');
      content.style.display = 'inline';
      this.materials = new Materials([], { caseStudyId: this.caseStudy.id, keyflowId: this.keyflowId });
      this.actors = new Actors([], { caseStudyId: this.caseStudy.id, keyflowId: this.keyflowId });
      this.activities = new Activities([], { caseStudyId: this.caseStudy.id, keyflowId: this.keyflowId });
      this.activityGroups = new ActivityGroups([], { caseStudyId: this.caseStudy.id, keyflowId: this.keyflowId });
      
      var loader = new Loader(content, {disable: true});
      $.when(this.materials.fetch(), this.actors.fetch(), 
             this.activities.fetch(), this.activityGroups.fetch()).then(function(){
        loader.remove();
        _this.renderMatFilter();
        _this.renderSankey();
      })
    },
    
    renderSankey: function(){
      var type = this.el.querySelector('#data-view-type-select').value;
      var collection = (type == 'actor') ? this.actors: 
                       (type == 'activity') ? this.activities: 
                       this.activityGroups;
      if (this.flowsView != null) this.flowsView.close();
      this.flowsView = new FlowSankeyView({
          el: document.getElementById('sankey-wrapper'),
          collection: collection,
          materials: this.materials,
          filter_params: this.filter_params,
        })
    },
    
    renderSankeyMap: function(){
      this.sankeyMap = new SankeyMap({
        divid: 'sankey-map', 
        nodes: '/static/data/nodes.geojson', 
        links: '/static/data/links.csv'
      });
    },
    
    renderMatFilter: function(){
      var _this = this;
      // select material
      var matSelect = document.createElement('div');
      matSelect.classList.add('materialSelect');
      this.hierarchicalSelect(this.materials, matSelect, {
        callback: function(model){
          if (model){
            _this.filter_params = { material: model.id };
            _this.renderSankey();
          }
        }
      });
      this.el.querySelector('#sub-filter').appendChild(matSelect);
    },
    
    // build a hierarchical selection of a collection, 
    // parent  of the models define tree structure
    // options.callback(model) is called, when a model from the collection is selected
    // options.selected preselects the model with given id
    hierarchicalSelect: function(collection, parent, options){
      var wrapper = document.createElement("div");
      var options = options || {};
      var items = [];
      
      // list to tree
      function treeify(list) {
        var treeList = [];
        var lookup = {};
        list.forEach(function(item) {
          lookup[item['id']] = item;
        });
        list.forEach(function(item) {
          if (item['parent'] != null) {
            lookupParent = lookup[item['parent']]
            if (!lookupParent['nodes']) lookupParent['nodes'] = [];
            lookupParent['nodes'].push(item);
          } else {
            treeList.push(item);
          }
        });
        return treeList;
      };
      
      // make a list out of the collection that is understandable by treeify and hierarchySelect
      collection.each(function(model){
        var item = {};
        var name = model.get('name');
        item.text = name.substring(0, 70);
        if (name.length > 70) item.text += '...';
        item.title = model.get('name');
        item.level = 1;
        item.id = model.id;
        item.parent = model.get('parent');
        item.value = model.id;
        items.push(item);
      })
      
      var treeList = treeify(items);
      
      // converts tree to list sorted by appearance in tree, 
      // stores the level inside the tree as an attribute in each node
      function treeToLevelList(root, level){
        var children = root['nodes'] || [];
        children = children.slice();
        delete root['nodes'];
        root.level = level;
        list = [root];
        children.forEach(function(child){
          list = list.concat(treeToLevelList(child, level + 1));
        })
        return list;
      };
      
      var levelList = [];
      treeList.forEach(function(root){ levelList = levelList.concat(treeToLevelList(root, 1)) });
      
      // load template and initialize the hierarchySelect plugin
      var inner = document.getElementById('hierarchical-select-template').innerHTML,
          template = _.template(inner),
          html = template({ options: levelList });
      wrapper.innerHTML = html;
      wrapper.name = 'material';
      parent.appendChild(wrapper);
      var select = wrapper.querySelector('.hierarchy-select');
      $(select).hierarchySelect({
          width: 400
      });
      
      // preselect an item
      if (options.selected){
        var selection = select.querySelector('.selected-label');
        var model = collection.get(options.selected);
        if (model){
          // unselect the default value
          var li = select.querySelector('li[data-default-selected]');
          li.classList.remove('active');
          selection.innerHTML = model.get('name');
          var li = select.querySelector('li[data-value="' + options.selected + '"]');
          li.classList.add('active');
        }
      }
      
      // event click on item
      var anchors = select.querySelectorAll('a');
      for (var i = 0; i < anchors.length; i++) {
        anchors[i].addEventListener('click', function(){
          var item = this.parentElement;
          var model = collection.get(item.getAttribute('data-value'));
          wrapper.title = item.title;
          if (options.callback) options.callback(model);
        })
      }
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
  return FlowsView;
}
);