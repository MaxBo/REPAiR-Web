define(['views/baseview', 'underscore',
        'collections/gdsecollection', 'models/indicator',
        'visualizations/map', 'openlayers', 'chroma-js', 'utils/utils',
        'muuri', 'app-config', 'highcharts'],

function(BaseView, _, GDSECollection, Indicator, Map, ol, chroma, utils, 
         Muuri, config, highcharts){
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
    * render workshop mode for flow assessment with chloropleth map and bar charts
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
        this.selectedAreas = [];
        this.chartData = [];

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
        'change select[name="indicator"]': 'computeMapIndicator',
        'change select[name="spatial-level-select"]': 'computeMapIndicator',
        'click #add-area-select-item-btn': 'addAreaSelectItem',
        'click button.remove-item': 'removeAreaSelectItem',
        'click button.select-area': 'showAreaModal',
        'click .area-select.modal .confirm': 'confirmAreaSelection',
        'change select[name="level-select"]': 'changeAreaLevel'
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
        this.levelSelect = this.el.querySelector('select[name="spatial-level-select"]');
        this.elLegend = this.el.querySelector('.legend');
        this.areaSelectRow = this.el.querySelector('#indicator-area-row');
        this.addAreaSelectBtn = this.el.querySelector('#add-area-select-item-btn');
        this.barChartRow = this.el.querySelector('#bar-chart');
        this.barChart = {};
        
        this.areaSelectGrid = new Muuri('#indicator-area-row', {
            dragAxis: 'x',
            layoutDuration: 400,
            layoutEasing: 'ease',
            dragEnabled: true,
            dragSortInterval: 0,
            dragReleaseDuration: 400,
            dragReleaseEasing: 'ease',
            layout: {
                fillGaps: false,
                horizontal: true,
                rounding: true
              }
        });
        this.areaSelectGrid.on('dragEnd', function (items) {
            _this.saveSession();
        });
        this.initIndicatorMap();
        this.renderAreaModal();
        this.addFocusAreaItem();
        this.restoreSession();
    },
    
    // compute and render the indicator on the map
    computeMapIndicator: function(){
        var indicatorId = this.indicatorSelect.value,
            levelId = this.levelSelect.value,
            _this = this;
        // one of the selects is not set to sth. -> nothing to render
        if (indicatorId == -1 || levelId == -1) return;
        
        var indicator = this.indicators.get(indicatorId);;
        
        function fetchCompute(areas){
            var areaIds = areas.pluck('id');
            
            indicator.compute({
                data: { areas: areaIds.join(',') },
                success: function(data){ 
                    _this.loader.deactivate();
                    _this.renderIndicatorOnMap(data, areas, indicator) 
                },
                error: _this.onError
            })
        }
        this.loader.activate();
        this.getAreas(levelId, fetchCompute);
    },
    
    // fetch the areas of given area level
    // call success(areas) on successful fetch
    getAreas: function(level, onSuccess){
        var areas = this.areas[level],
            _this = this;
        if (areas != null) {
            onSuccess(areas);
            return;
        }
        areas = this.areas[level] = new GDSECollection([], { 
            apiTag: 'areas',
            apiIds: [ this.caseStudy.id, level ]
        });
        areas.fetch({
            success: function(areas){
                var promises = [];
                areas.forEach(function(area){
                    promises.push(
                        area.fetch({ error: _this.onError })
                    )
                });
                Promise.all(promises).then(function(){
                    onSuccess(areas);
                });
            },
            error: this.onError
        });
    },
    
    // render given indicator and its data into the areas into the chlorpleth map
    renderIndicatorOnMap: function(data, areas, indicator){
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
            entries = (step > 0) ? utils.range(minValue, maxValue, step): [0];
            
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
    
    saveSession: function(){
        var items = this.areaSelectGrid.getItems(),
            _this = this;
        var orderedSelects = [];
        items.forEach(function(item){
            var id = item.getElement().dataset['id'];
            // Focus Area has id 0, skip it
            if (id > 0){
                var areaSelect = Object.assign({}, _this.areaSelects[id]);
                areaSelect.id = id;
                orderedSelects.push(areaSelect);
            }
        });
        config.session.save({areaSelects: orderedSelects});
    },
    
    restoreSession: function(){
        var orderedSelects = config.session.get('areaSelects'),
            _this = this;
        this.areaSelects = {};
        if (!orderedSelects || orderedSelects.length == 0) return;
        _this.renderBarChart(_this.barChartRow);
        orderedSelects.forEach(function(areaSelect){
            var id = areaSelect.id;
            areaSelect = Object.assign({}, areaSelect);
            delete areaSelect.id;
            _this.areaSelects[id] = areaSelect;
            _this.areaSelectIdCnt = Math.max(_this.areaSelectIdCnt, parseInt(id) + 1);
            _this.renderAreaBox(_this.areaSelectRow, id, id);
            _this.addBarChartData(id);
            
            var button = _this.el.querySelector('button.select-area[data-id="' + id + '"]'),
                areas = areaSelect.areas;
            if (areas.length > 0){
                button.classList.remove('btn-warning');
                button.classList.add('btn-primary');
            } else {
                button.classList.add('btn-warning');
                button.classList.remove('btn-primary');
            }
        
        })
    },
    
    // render item for area selection
    renderAreaBox: function(el, id, title, fontSize){
        var html = document.getElementById('row-box-template').innerHTML,
            template = _.template(html),
            div = document.createElement('div');
        div.innerHTML = template({
            title: title, 
            fontSize: fontSize || '60px',
            id: id
        });
        div.classList.add('item');
        el.appendChild(div);
        //el.insertBefore(div, this.addAreaSelectBtn);
        div.dataset['id'] = id;
        this.areaSelectGrid.add(div, {});

        return div;
    },

    // render item for bar chart
    renderBarChart: function(el){
        var div = document.createElement('div');
        el.appendChild(div);
        
        //create bar chart
        this.barChart = highcharts.chart(div, {
            chart: {
                type: 'column'
            },
            xAxis: {
                min: 0
            },
            yAxis: {
                min: 0
            },
            title: '',
            legend: {
                enabled: false
            },
            series: [{
                data: []
            }]
        });
    },
    
    // add data to bar chart
    addBarChartData: function(id){
        var areas = this.areaSelects[id];
        // build url and get the data for the bar chart
        var urlind = config.api.flowIndicators;
        urlind += "{2}/compute?areas=";
        for(area in areas){
            urlind += area + ",";
        }
        // remove trailing comma
        urlind.slice(0,-1);
        
        if (areas !== undefined && areas.length != 0) {
            var url = urlind.format(this.caseStudy.id, this.keyflowId, this.indicatorSelect.value);
            $.ajax({
                url: url,
                type: 'GET',
                async: true,
                dataType: "json",
                success: function (data) {
                    var sum = 0;
                    $.each(data.results, function(index, value) {
                        sum += value.value;
                    });
                    this.chartData.push([id, sum]);
                }
            });
        }
        //test
        this.barChart.series[0].setData([[1,1], [2,2], [4,5]]);
        //this.barChart.series[0].setData(this.chartData);
    },
    
    // render an item where the user can setup areas to be shown as bar charts
    addAreaSelectItem: function(){
        var id = this.areaSelectIdCnt;
        this.renderAreaBox(
            this.areaSelectRow, id, id);
        this.areaSelects[id] = {
            areas: [],
            level: this.areaLevels.first().id
        }
        this.areaSelectIdCnt += 1;
        this.addBarChartData(id);
        this.saveSession();
    },
    
    // item for focus area
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
    
    // remove an area item
    removeAreaSelectItem: function(evt){
        var id = evt.target.dataset['id'],
            div = this.areaSelectRow.querySelector('div.item[data-id="' + id + '"]');
        delete this.areaSelects[id];
        this.areaSelectGrid.remove(div, { removeElements: true });
        
        //remove bar chart with it
        //TODO: Remove data from this.chartData
        this.saveSession();
    },
    
    // initialize the chlorpleth map
    initIndicatorMap: function(){
        var _this = this;
        this.map = new Map({
            el: document.getElementById('indicator-map')
        });
        var focusarea = this.caseStudy.get('properties').focusarea;

        // add polygon of focusarea to both maps and center on their centroid
        if (focusarea != null){
            var poly = new ol.geom.Polygon(focusarea.coordinates[0]);
            this.map.centerOnPolygon(poly, { projection: this.projection });
        };
    },
    
    // render the modal for area selections
    renderAreaModal: function(){
        this.areaModal = this.el.querySelector('.area-select.modal');
        var html = document.getElementById('area-select-modal-template').innerHTML,
            template = _.template(html),
            _this = this;
        this.areaModal.innerHTML = template({ levels: this.areaLevels });
        this.areaLevelSelect = this.areaModal.querySelector('select[name="area-level-select"]');
        this.areaMap = new Map({
            el: this.areaModal.querySelector('.map'), 
        });
        this.areaMap.addLayer(
            'areas', 
            { 
                stroke: 'rgb(100, 150, 250)', 
                fill: 'rgba(100, 150, 250, 0.5)',
                select: {
                    selectable: true,
                    stroke: 'rgb(230, 230, 0)', 
                    fill: 'rgba(230, 230, 0, 0.5)',
                    onChange: function(areaFeats){
                        var modalSelDiv = _this.el.querySelector('.selections'),
                            levelId = _this.areaLevelSelect.value
                            labels = [],
                            areas = _this.areas[levelId];
                        _this.selectedAreas = [];
                        areaFeats.forEach(function(areaFeat){
                            labels.push(areaFeat.label);
                            _this.selectedAreas.push(areaFeat.id);
                        });
                        modalSelDiv.innerHTML = labels.join(', ');
                    }
                }
            }
        );
        // event triggered when modal dialog is ready -> trigger rerender to match size
        $(this.areaModal).on('shown.bs.modal', function () {
            _this.areaMap.map.updateSize();
        });
    },
    
    // show the modal for area selections
    showAreaModal: function(evt){
        var id = evt.target.dataset['id'],
            level = this.areaSelects[id].level,
            _this = this;
        this.selectedAreas = [];
        this.activeAreaSelectId = id;
        this.areaLevelSelect.value = level;
        var labels = [];
        function selectAreas(){
            _this.areaSelects[id].areas.forEach(function(areaId){
                var area = _this.areas[level].get(areaId);
                labels.push(area.get('name'));
                _this.areaMap.selectFeature('areas', area.id);
            })
        }
        this.drawAreas(level, selectAreas);
        this.el.querySelector('.selections').innerHTML = labels.join(', ');
        $(this.areaModal).modal('show');
    },
    
    // event listener for change the area level inside the area selection modal
    changeAreaLevel: function(evt){
        var level = evt.target.value;
        this.selectedAreas = [];
        this.el.querySelector('.selections').innerHTML = '';
        this.drawAreas(level);
    },

    // draw the areas of given level into the map of the area selection modal
    drawAreas: function(level, onSuccess){
        var _this = this;
        this.areaMap.clearLayer('areas');
        var loader = new utils.Loader(this.areaModal, {disable: true});
        function draw(areas){
            areas.forEach(function(area){
                var coords = area.get('geometry').coordinates,
                    name = area.get('name');
                _this.areaMap.addPolygon(coords, { 
                    projection: 'EPSG:4326', layername: 'areas', 
                    type: 'MultiPolygon', tooltip: name,
                    label: name, id: area.id
                });
            })
            loader.deactivate();
            _this.areaMap.centerOnLayer('areas');
            if(onSuccess) onSuccess();
        }
        loader.activate();
        this.getAreas(level, draw);
    },
    
    // user confirmation of selected areas in modal
    confirmAreaSelection: function(){
        var id = this.activeAreaSelectId;
        this.areaSelects[id].areas = this.selectedAreas;
        this.areaSelects[id].level = this.areaLevelSelect.value;
        var button = this.el.querySelector('button.select-area[data-id="' + id + '"]')
        if (this.selectedAreas.length > 0){
            button.classList.remove('btn-warning');
            button.classList.add('btn-primary');
        } else {
            button.classList.add('btn-warning');
            button.classList.remove('btn-primary');
        }
        this.saveSession();
    }
    
});
return FlowAssessmentWorkshopView;
}
);