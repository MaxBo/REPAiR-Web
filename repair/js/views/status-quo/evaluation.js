define(['backbone', 'underscore', 'visualizations/map', 'utils/utils'],

function(Backbone, _, Map, utils){
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
            _.bindAll(this, 'categoryChanged');

            this.template = options.template;
            this.caseStudy = options.caseStudy;
            this.projection = 'EPSG:4326'; 

            this.categories = ['Social', 'Economic', 'Environmental']

            this.indicators = {
                'Social': [],
                'Economic': ['Effectiveness in achieving behaviour change', 
                'Public acceptance','Urban space consumption',
                'Not in my backyard syndrome','Odour',
                'Stakeholder involvement','Access to green spaces','Accessability / convenience of us of the WM system',
                'Private space consumption','Visual impacts','Risk perception','Total employment','Inconveniences because of waste management','Mobility (traffic jams)','Noise'],
                'Environmental': []
            }

            this.render();
        },

        /*
        * dom events (managed by jquery)
        */
        events: {
            'change #category-select': 'categoryChanged'
        },

        /*
        * render the view
        */
        render: function(){
            var _this = this;
            var html = document.getElementById(this.template).innerHTML
            var template = _.template(html);
            this.el.innerHTML = template({ categories: this.categories});

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

        categoryChanged: function(evt){
            var impactSelect = this.el.querySelector('#indicator-select');
            utils.clearSelect(impactSelect);
            var category = evt.target.value,
                indicators = this.indicators[category];
            console.log(document.getElementById('category-select').value);
            console.log(this.indicators)
            indicators.forEach(function(indicator){
                var option = document.createElement('option');
                option.text = indicator;
                impactSelect.appendChild(option);
            })
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