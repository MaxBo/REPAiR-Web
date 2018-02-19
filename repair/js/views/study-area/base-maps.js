define(['backbone', 'underscore', 'visualizations/map', 'utils/loader', 
        'app-config', 'bootstrap-colorpicker'],

function(Backbone, _, Map, Loader, config){
  /**
   *
   * @author Christoph Franke
   * @name module:views/BaseMapsView
   * @augments Backbone.View
   */
  var BaseMapsView = Backbone.View.extend(
    /** @lends module:views/BaseMapsView.prototype */
    {

    /**
     * render view to add layers to casestudy
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
      
      this.template = options.template;
      this.caseStudy = options.caseStudy;
      
      var GeoLayers = Backbone.Collection.extend({ url: config.geoserverApi.layers })
      
      this.geoLayers = new GeoLayers();
      
      //this.categories = [{name: 'Test1', id: 1, 'Test2']
      
      var loader = new Loader(this.el, {disable: true});
      this.geoLayers.fetch({ success: function(){
        loader.remove();
        _this.render();
      }});
    },

    /*
      * dom events (managed by jquery)
      */
    events: {
      'click #add-layer-button': 'addLayer',
      'click #add-layer-modal .confirm': 'confirmLayer'
    },

    /*
      * render the view
      */
    render: function(){
      var _this = this;
      var html = document.getElementById(this.template).innerHTML
      var template = _.template(html);
      this.el.innerHTML = template();
      this.renderMap();
      this.renderAvailableLayers();
    },
    
    renderMap: function(){
      var map = new Map({
        divid: 'base-map', 
      });
      map.addLayer('test', { source: { url: '/geoserver/ows' } })
    },
    
    /*
     * render the hierarchic tree of layers
     */
    renderDataTree: function(selectId){
    
      var _this = this;
      var dataDict = {};
      
      
      
    },
    
    renderAvailableLayers: function(){
      var _this = this;
      
      $('#colorpicker').colorpicker().on('changeColor',
        function(ev) { this.style.backgroundColor = this.value; }
      );
      colorpicker.value = '#ffffff';
      var rows = [];
      var table = document.getElementById('available-layers-table');
      
      this.geoLayers.each(function(layer){
        var row = table.getElementsByTagName('tbody')[0].insertRow(-1);
        row.insertCell(-1).innerHTML = '';
        row.insertCell(-1).innerHTML = layer.get('name');
        rows.push(row);
        
        row.style.cursor = 'pointer';
        row.addEventListener('click', function() {
          _.each(rows, function(r){
            r.classList.remove('selected');
          });
          row.classList.add('selected');
          _this.selectedGeoLayer = layer;
        });
      });
      
    },
    
    addLayer: function(){
      var modal = document.getElementById('add-layer-modal');
      $(modal).modal('show'); 
    },
    
    confirmLayer: function(){
      if (!this.selectedGeoLayer) return;
      
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
  return BaseMapsView;
}
);