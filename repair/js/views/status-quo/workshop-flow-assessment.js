define(['views/baseview', 'underscore',
        'collections/gdsecollection', 'models/indicator',
        'visualizations/map', 'openlayers'],

function(BaseView, _, GDSECollection, Indicator, Map, ol){
/**
*
* @author Christoph Franke
* @name module:views/FlowAssessmentWorkshopView
* @augments module:views/BaseView
*/
var FlowAssessmentWorkshopView = BaseView.extend(
    /** @lends module:views/FlowsView.prototype */
    {

    /**
    * render workshop mode for flow assessment
    *
    * @param {Object} options
    * @param {HTMLElement} options.el                     element the view will be rendered in
    * @param {string} options.template                    id of the script element containing the underscore template to render this view
    * @param {module:models/CaseStudy} options.caseStudy  the casestudy to add layers to
    *
    * @constructs
    * @see http://backbonejs.org/#View
    */
    initialize: function(options){
        FlowAssessmentWorkshopView.__super__.initialize.apply(this, [options]);
        var _this = this;
        
        this.caseStudy = options.caseStudy;
        this.keyflowId = options.keyflowId;
        this.indicators = new GDSECollection([], { 
            apiTag: 'flowIndicators',
            apiIds: [this.caseStudy.id, this.keyflowId ],
            comparator: 'name',
            model: Indicator
        });
        this.areaLevels = new GDSECollection([], { 
            apiTag: 'arealevels',
            apiIds: [this.caseStudy.id],
            comparator: 'level'
        });
        this.areas = {};

        this.loader.activate();
        var promises = [
            this.indicators.fetch(),
            this.areaLevels.fetch()
        ]
        Promise.all(promises).then(function(){
            _this.indicators.sort();
            _this.loader.deactivate();
            _this.render();
        })
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'change select[name="indicator"]': 'computeIndicator',
        'change select[name="level-select"]': 'computeIndicator'
    },

    /*
    * render the view
    */
    render: function(){
        var _this = this;
        var html = document.getElementById(this.template).innerHTML
        var template = _.template(html);
        this.el.innerHTML = template({indicators: this.indicators, 
                                      levels: this.areaLevels});
        this.indicatorSelect = this.el.querySelector('select[name="indicator"]');
        this.levelSelect = this.el.querySelector('select[name="level-select"]');
        this.renderMap();
    },
    
    computeIndicator: function(){
        var indicatorId = this.indicatorSelect.value,
            levelId = this.levelSelect.value,
            _this = this;
        // one of the selects is not set to sth. -> nothing to render
        if (indicatorId == -1 || levelId == -1) return;
        
        var indicator = this.indicators.get(indicatorId);;
        
        function fetchCompute(areas){
            var areaIds = areas.pluck('id');
            console.log(areaIds)
            indicator.compute({
                data: { areas: areaIds.join(',') },
                success: function(data){ _this.renderIndicator(data, areas) },
                error: _this.onError
            })
        }
        
        var areas = this.areas[levelId];
        if (areas == null){
            areas = this.areas[levelId] = new GDSECollection([], { 
                apiTag: 'areas',
                apiIds: [ this.caseStudy.id, levelId ]
            });
            this.loader.activate();
            areas.fetch({
                success: function(areas){
                    var promises = [];
                    areas.forEach(function(area){
                        promises.push(
                            area.fetch({ error: _this.onError })
                        )
                    });
                    Promise.all(promises).then(function(){
                        _this.loader.deactivate();
                        fetchCompute(areas);
                    });
                },
                error: this.onError
            });
        }
        else fetchCompute(areas)
    },
    
    renderIndicator: function(data, areas){
        console.log(data)
        var _this = this,
            values = {};
        data.forEach(function(d){
            values[d.area] = d.value;
        })
        areas.forEach(function(area){
            var coords = area.get('geometry').coordinates,
                name = area.get('name'),
                value = values[area.id]
            _this.map.addPolygon(coords, { 
                projection: 'EPSG:4326', layername: 'areas', 
                type: 'MultiPolygon', tooltip: name + ': ' + value,
                label: value + '', id: area.id
            });
        })
        this.map.centerOnLayer('areas');
    },
    
    renderMap: function(){
        var _this = this;
        this.map = new Map({
            divid: 'indicator-map'
        });
        var focusarea = this.caseStudy.get('properties').focusarea;

        // add polygon of focusarea to both maps and center on their centroid
        if (focusarea != null){
            var poly = new ol.geom.Polygon(focusarea.coordinates[0]);
            this.map.centerOnPolygon(poly, { projection: this.projection });
        };
        this.map.addLayer(
            'areas', 
            { 
                stroke: 'rgb(100, 150, 250)', 
                fill: 'rgba(100, 150, 250, 0.5)',
            }
        );
    },
    
});
return FlowAssessmentWorkshopView;
}
);