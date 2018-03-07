define(['backbone', 'underscore','collections/flows',
        'collections/stocks', 'visualizations/sankey', 
        'collections/activities', 'collections/actors',
        'utils/loader'],

function(Backbone, _, Flows, Stocks, Sankey, Activities, Actors, Loader){

  /**
   *
   * @author Christoph Franke
   * @name module:views/FlowsView
   * @augments Backbone.View
   */
  var FlowSankeyView = Backbone.View.extend( 
    /** @lends module:views/FlowsView.prototype */
    {

    /**
     * render view to edit flows of a single keyflow
     *
     * @param {Object} options
     * @param {HTMLElement} options.el                          element the view will be rendered in
     * @param {module:collections/Keyflows.Model} options.model the keyflow (defining the type of flows that will be rendered)
     * @param {Object=} options.filterParams  parameters to filter the flows and stocks with (e.g. {material: 1})
     * @param {boolean} [options.hideUnconnected=false]  hide nodes that don't have in or outgoing flows or stocks (filtered by filterParams)
     * @param {module:collections/ActivityGroups|module:collections/ActivityGroups|module:collections/Actors} options.model the nodes to render
     *
     * @constructs
     * @see http://backbonejs.org/#View
     */
    initialize: function(options){
      _.bindAll(this, 'render');
      _.bindAll(this, 'toggleFullscreen');
      var _this = this;
      this.caseStudyId = options.caseStudyId || this.collection.caseStudyId;
      this.keyflowId = options.keyflowId || this.collection.keyflowId;
      this.materials = options.materials;
      this.hideUnconnected = options.hideUnconnected;
      
      var type = (this.collection instanceof Actors) ? 'actor': 
                 (this.collection instanceof Activities) ? 'activity': 'activitygroup';
      this.flows = new Flows([], {caseStudyId: this.caseStudyId,
                                  keyflowId: this.keyflowId,
                                  type: type});
      this.stocks = new Stocks([], {caseStudyId: this.caseStudyId,
                                    keyflowId: this.keyflowId,
                                    type: type});
                                    
      var loader = new Loader(this.el, {disable: true});
      $.when(this.stocks.fetch({data: options.filterParams}), this.flows.fetch({data: options.filterParams})).then(function(){
        _this.render();
        loader.remove();
      });
    },

    /*
     * dom events (managed by jquery)
     */
    events: {
      'click a[href="#flow-map-panel"]': 'refreshMap',
      'click #fullscreen-toggle': 'toggleFullscreen',
      'change #data-view-type-select': 'renderSankey'
    },
 
    /*
     * render the view
     */
    render: function(){
      this.sankeyData = this.transformData(this.collection, this.flows, this.stocks, this.materials);
      var fullscreenBtn = document.createElement('button');
      fullscreenBtn.classList.add("glyphicon", "glyphicon-fullscreen", "btn", "btn-primary", "fullscreen-toggle");
      fullscreenBtn.addEventListener('click', this.toggleFullscreen);
      this.el.appendChild(fullscreenBtn);
      var width = this.el.clientWidth;
      var height = this.el.classList.contains('fullscreen') ?
                   this.el.clientHeight: width / 3;
      var div = this.el.querySelector('.sankey');
      if (div == null){
        div = document.createElement('div');
        div.classList.add('sankey', 'bordered');
        this.el.appendChild(div);
      }
      var sankey = new Sankey({
        height: height,
        width: width,
        el: div,
        title: ''
      })
      sankey.render(this.sankeyData);
    },
  
    /*
     * render sankey-diagram in fullscreen
     */
    toggleFullscreen: function(){
      this.el.classList.toggle('fullscreen');
      this.render();
    },
    
    /*
     * transform the models, their links and the stocks to a json-representation
     * readable by the sankey-diagram
     */
    transformData: function(models, flows, stocks, materials){
      var _this = this;
      var nodes = [];
      var nodeIdxDict = {}
      var i = 0;
      
      models.forEach(function(model){
        var id = model.id;
        var name = model.get('name');
        // ignore nodes with no connections at all (if requested)
        if (_this.hideUnconnected) {
          if (flows.nConnections(id) == 0 && stocks.nConnections(id) == 0)
            return;
        }
        nodes.push({ id: id, name: name });
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
              var material = materials.get(fraction.material);
              text += fraction.fraction * 100 + '% ';
              text += material.get('name');
              if (i < fractions.length - 1) text += '\n';
              i++;
            })
          }
        return text || ('no composition defined')
      }
      
      flows.forEach(function(flow){
        var value = flow.get('amount');
        var originId = flow.get('origin'),
            destinationId = flow.get('destination'),
            source = nodeIdxDict[originId],
            target = nodeIdxDict[destinationId];
        // continue if one of the linked nodes does not exist
        if (source == null || target == null) return false;
        var composition = flow.get('composition');
        links.push({
          value: flow.get('amount'),
          units: gettext('t/year'),
          source: source,
          target: target,
          text: compositionRepr(composition)
        });
      })
      stocks.forEach(function(stock){
        var id = 'stock-' + stock.id;
        var originId = stock.get('origin'),
            source = nodeIdxDict[originId];
        // continue if node does not exist
        if (source == null) return false;
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
  return FlowSankeyView;
}
);