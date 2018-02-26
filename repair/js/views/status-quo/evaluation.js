define(['backbone', 'underscore', 'visualizations/map'],

function(Backbone, _, Map){
    /**
    *
    * @author Christoph Franke
    * @name module:views/EvaluationView
    * @augments Backbone.View
    */
    var EvaluationView = Backbone.View.extend(
        /** @lends module:views/EvaluationView.prototype */
        {

        /**
        * render setup view on the evaluation
        *
        * @param {Object} options
        * @param {HTMLElement} options.el                      element the view will be rendered in
        * @param {string} options.template                     id of the script element containing the underscore template to render this view
        * @param {module:models/CaseStudy} options.caseStudy   the casestudy
        *
        * @constructs
        * @see http://backbonejs.org/#View
        */
        initialize: function(options){
            var _this = this;
            _.bindAll(this, 'render');

            this.template = options.template;
            this.caseStudy = options.caseStudy;
            this.projection = 'EPSG:4326'; 
            this.render();
        },

        /*
        * dom events (managed by jquery)
        */
        events: {
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
        },
    
        renderMap: function(){
          this.map = new Map({
            divid: 'evaluation-map', 
          });
          var focusarea = this.caseStudy.get('properties').focusarea;
          
          this.map.addLayer('background', {
              stroke: '#aad400',
              fill: 'rgba(170, 212, 0, 0.1)',
              strokeWidth: 1,
              zIndex: 0
            },
          );
          // add polygon of focusarea to both maps and center on their centroid
          if (focusarea != null){
            var poly = this.map.addPolygon(focusarea.coordinates[0], { projection: this.projection, layername: 'background', tooltip: gettext('Focus area') });
            this.map.addPolygon(focusarea.coordinates[0], { projection: this.projection, layername: 'background', tooltip: gettext('Focus area') });
            this.centroid = this.map.centerOnPolygon(poly, { projection: this.projection });
            this.map.centerOnPolygon(poly, { projection: this.projection });
          };
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
    return EvaluationView;
}
);