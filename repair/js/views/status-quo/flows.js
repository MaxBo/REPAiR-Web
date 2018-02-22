define(['backbone', 'underscore', 'visualizations/sankey-map',
        'collections/keyflows', 'collections/materials', 
        'collections/actors', 'collections/activitygroups',
        'collections/activities', 'collections/flows',
        'collections/stocks', 'visualizations/sankey', 'utils/loader',
        'hierarchy-select'],

function(Backbone, _, SankeyMap, Keyflows, Materials, Actors, ActivityGroups, 
         Activities, Flows, Stocks, Sankey, Loader){
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
      
      this.keyflows = new Keyflows([], { caseStudyId: this.caseStudy.id })
      
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
      'click #fullscreen-toggle': 'toggleFullscreen',
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
    
    renderSankeyMap: function(){
      this.sankeyMap = new SankeyMap({
        divid: 'sankey-map', 
        nodes: '/static/data/nodes.geojson', 
        links: '/static/data/links.csv'
      });
    },
    
    /*
     * render sankey-diagram in fullscreen
     */
    toggleFullscreen: function(){
      document.getElementById('sankey-wrapper').classList.toggle('fullscreen');
      this.renderSankey({skipFetch: true});
    },
    
    renderMatFilter: function(){
    
      // select material
      var matSelect = document.createElement('div');
      matSelect.classList.add('materialSelect');
      this.hierarchicalSelect(this.materials, matSelect, {
        callback: function(model){
          var matId = (model) ? model.id : '';
          matSelect.setAttribute('data-material-id', matId);
          setCustom();
        }
      });
      this.el.querySelector('#sub-filter').appendChild(matSelect);
    },
    
    // build a hierarchical selection of a collection, 
    // parent  of the models define tree structure
    // options.callback(model) is called, when a model from the collection is selected
    // options.selected preselects the model with given id
    hierarchicalSelect: function(collection, parent, options){
      console.log(collection)
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
      console.log(treeList)
      
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
        this.flows = new Flows([], {caseStudyId: this.caseStudy.id,
                                    keyflowId: this.keyflowId,
                                    type: type});
        this.stocks = new Stocks([], {caseStudyId: this.caseStudy.id,
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
            var i = 0;
            fractions.forEach(function(fraction){
              var material = _this.materials.get(fraction.material);
              text += fraction.fraction * 100 + '% ';
              text += material.get('name');
              if (i < fractions.length - 1) text += '\n';
              i++;
            })
          }
        return text || ('no composition defined')
      }
      
      flows.each(function(flow){
        var value = flow.get('amount');
        var source = nodeIdxDict[flow.get('origin')];
        var target = nodeIdxDict[flow.get('destination')];
        var composition = flow.get('composition');
        
        links.push({
          value: flow.get('amount'),
          units: gettext('t/year'),
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
          units: gettext('t/year'),
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