define(['views/baseview', 'underscore',
        'collections/gdsecollection', 'models/indicator',
        'visualizations/map', 'openlayers', 'chroma-js', 'utils/utils'],

function(BaseView, _, GDSECollection, Indicator, Map, ol, chroma, utils){
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
        this.areaSelects = {};
        this.areaSelectIdCnt = 0;

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
        'change select[name="level-select"]': 'computeIndicator',
        'click #add-area-select-item-btn': 'addAreaSelectItem',
        'click button.remove-item': 'removeAreaSelectItem',
        'click button.select-area': 'selectArea'
    },

    /*
    * render the view
    */
    render: function(){
        var _this = this,
            html = document.getElementById(this.template).innerHTML,
            template = _.template(html);
        this.el.innerHTML = template({indicators: this.indicators, 
                                      levels: this.areaLevels});
        this.indicatorSelect = this.el.querySelector('select[name="indicator"]');
        this.levelSelect = this.el.querySelector('select[name="level-select"]');
        this.elLegend = this.el.querySelector('.legend');
        this.areaSelectRow = this.el.querySelector('#indicator-area-row');
        this.addAreaSelectBtn = this.el.querySelector('#add-area-select-item-btn');
        
        this.renderMap();
        this.addFocusAreaItem();
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
            _this.loader.activate();
            indicator.compute({
                data: { areas: areaIds.join(',') },
                success: function(data){ 
                    _this.loader.deactivate();
                    _this.renderIndicator(data, areas, indicator) 
                },
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
    
    renderIndicator: function(data, areas, indicator){
        var _this = this,
            values = {},
            minValue = 0,
            maxValue = 0,
            unit = indicator.get('unit');
        data.forEach(function(d){
            var value = Math.round(d.value)
            values[d.area] = value;
            maxValue = Math.max(value, maxValue);
            minValue = Math.min(value, minValue);
        })
        
        var colorRange = chroma.scale(['#edf8b1', '#7fcdbb', '#2c7fb8']) //'Spectral')//['yellow', 'navy'])
                               .domain([minValue, maxValue]);
        var step = (maxValue - minValue) / 10,
            entries = utils.range(minValue, maxValue, step);
            
        this.elLegend.innerHTML = '';
        entries.forEach(function(entry){
            var color = colorRange(entry).hex(),
                square = document.createElement('div'),
                label = document.createElement('label');
            square.style.height = '25px';
            square.style.width = '50px';
            square.style.float = 'left';
            square.style.backgroundColor = color;
            label.innerHTML = Math.round(entry) + ' ' + unit;
            _this.elLegend.appendChild(square);
            _this.elLegend.appendChild(label);
            _this.elLegend.appendChild(document.createElement('br'));
        })
        this.map.addLayer(
            'areas', 
            { 
                stroke: 'rgb(100, 150, 250)',
                //strokeWidth: 3,
                fill: 'rgba(100, 150, 250, 0.5)',
                colorRange: colorRange,
                //alphaFill: 0.8
            }
        );
        areas.forEach(function(area){
            var coords = area.get('geometry').coordinates,
                name = area.get('name'),
                value = values[area.id]
            _this.map.addPolygon(coords, { 
                projection: 'EPSG:4326', layername: 'areas', 
                type: 'MultiPolygon', tooltip: name + ': ' + value + ' ' + unit,
                label: value + ' ' + unit, id: area.id,
                value: value
            });
        })
        this.map.centerOnLayer('areas');
    },
    
    renderAreaBox: function(el, id, title, fontSize){
        var html = document.getElementById('row-box-template').innerHTML,
            template = _.template(html),
            div = document.createElement('div');
        div.innerHTML = template({
            title: title, 
            fontSize: fontSize || '60px',
            id: id
        });
        el.insertBefore(div, this.addAreaSelectBtn);
        div.classList.add('item');
        div.dataset['id'] = id;
        return div;
    },
    
    addAreaSelectItem: function(){
        this.renderAreaBox(
            this.areaSelectRow, this.areaSelectIdCnt, this.areaSelectIdCnt);
        this.areaSelectIdCnt += 1;
    },
    
    addFocusAreaItem: function(){
        var div = this.renderAreaBox(
                this.areaSelectRow, this.areaSelectIdCnt, 
                'Focus <br> Area', '40px'
            ),
            buttons = div.querySelectorAll('button');
        this.areaSelectIdCnt += 1
        for(var i = 0; i < buttons.length; i++)
            buttons[i].style.display = 'none';
    },
    
    removeAreaSelectItem: function(evt){
        var id = evt.target.dataset['id'],
            div = this.areaSelectRow.querySelector('div.item[data-id="' + id + '"]');
        this.areaSelectRow.removeChild(div);
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
    },
    
});
return FlowAssessmentWorkshopView;
}
);