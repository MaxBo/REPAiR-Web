define(['views/common/baseview', 'underscore',
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
        _.bindAll(this, 'renderIndicator');
        _.bindAll(this, 'addAreaSelectItem');
        this.caseStudy = options.caseStudy;
        this.keyflowId = options.keyflowId;

        this.spatialItemColor = '#aad400';
        this.indicators = new GDSECollection([], {
            apiTag: 'flowIndicators',
            apiIds: [this.caseStudy.id, this.keyflowId],
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
        this.areaSelectIdCnt = 1;
        this.selectedAreas = [];
        this.chartData = {};

        this.mapColorRange = chroma.scale(['#edf8b1', '#7fcdbb', '#2c7fb8']); //'Spectral')//['yellow', 'navy'])
        // ToDo: replace with another scale
        this.barChartColor = utils.colorByName;

        this.loader.activate();
        var promises = [
            this.indicators.fetch({ data: { included: "True" } }),
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
        'change select[name="indicator"]': 'changeIndicator',
        'change select[name="spatial-level-select"]': 'computeMapIndicator',
        'click #add-area-select-item-btn': 'onAddAreaSelect',
        'click button.remove-item': 'removeAreaSelectItem',
        'click button.select-area': 'showAreaModal',
        'click .area-select.modal .confirm': 'confirmAreaSelection',
        'change select[name="area-level-select"]': 'changeAreaLevel'
    },

    /*
    * render the view
    */
    render: function(){
        var _this = this;
        _.bindAll(this, 'updateBarChart');
        var html = document.getElementById(this.template).innerHTML,
            template = _.template(html);
        this.el.innerHTML = template({indicators: this.indicators,
                                      levels: this.areaLevels});

        this.indicatorSelect = this.el.querySelector('select[name="indicator"]');
        this.indicatorId = this.indicatorSelect.value;
        this.levelSelect = this.el.querySelector('select[name="spatial-level-select"]');
        this.elLegend = this.el.querySelector('.legend');
        this.areaSelectRow = this.el.querySelector('#indicator-area-row');
        this.addAreaSelectBtn = this.el.querySelector('#add-area-select-item-btn');
        this.barChart = this.el.querySelector('#bar-chart');
        this.chart = {};

        // select a default area level (the middle one)
        if(this.areaLevels.length > 0){
            var idx = Math.floor(this.areaLevels.length / 2);
            this.levelSelect.selectedIndex = idx;
        }
        this.showSpatialItem = true;

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
              },
            dragStartPredicate: function (item, event) {
              // Prevent first item (Focus Area) from being dragged
              var id = parseInt(item.getElement().dataset['id']);
              if (id === 0) {
                return false;
              }
              return Muuri.ItemDrag.defaultStartPredicate(item, event);
            }
        });
        this.areaSelectGrid.on('dragEnd', function (item) {
            // you may drag items in front of focus area, move it to 2nd position
            var dragPos = _this.areaSelectGrid.getItems().indexOf(item);
            if (dragPos === 0){
                var id = item.getElement().dataset['id'];
                if ( id !== 0 )
                    _this.areaSelectGrid.move(item, 1);
            }
            _this.saveSession();
            _this.updateBarChart();
        });

        this.initIndicatorMap();
        this.renderAreaModal();
        this.addSpatialItem();
        this.computeMapIndicator();
        this.renderBarChart();
        this.restoreSession();
    },

    // fetch and show selected indicator
    changeIndicator: function(){
        var selected = this.indicatorSelect.value,
            indicator = this.indicators.get(selected);
        this.indicatorId = indicator.id;
        if(this.chartData[this.indicatorId] == undefined){
            this.chartData[this.indicatorId] = [];
        }
        if (indicator){
            // fetch the indicator to reload it
            indicator.fetch({
                success: this.renderIndicator,
                error: this.onError
            })
        }
        var label = this.el.querySelector('#indicator-description');
        label.innerHTML = indicator.get('description');
    },

    /*
    * render view on given indicator
    */
    renderIndicator: function(){
        this.computeMapIndicator();
        var orderedSelects = this.getOrderedSelects();
        this.addBarChartData(orderedSelects);
    },

    // compute and render the indicator on the map
    computeMapIndicator: function(){
        var levelId = this.levelSelect.value,
            _this = this;
        // one of the selects is not set to sth. -> nothing to render
        if (this.indicatorId == -1 || levelId == -1) return;

        var indicator = this.indicators.get(this.indicatorId);;

        var mapTab = this.el.querySelector('#indicator-map-tab'),
            mapLoader = new utils.Loader(mapTab, {disable: true});
        function fetchCompute(areas){
            var areaIds = areas.pluck('id');

            indicator.compute({
                method: "POST",
                data: { areas: areaIds.join(',') },
                success: function(data){
                    mapLoader.deactivate();
                    _this.renderIndicatorOnMap(data, areas, indicator)
                },
                error: _this.onError
            })
        }
        mapLoader.activate();
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
            success: onSuccess,
            error: this.onError
        });
    },

    // render given indicator and its data into the areas into the chlorpleth map
    renderIndicatorOnMap: function(data, areas, indicator){
        var _this = this,
            values = {},
            minValue = 0,
            maxValue = 0,
            unit = indicator.get('unit'),
            sr = indicator.get('spatial_reference');
        //this.map.setVisible('focusarea', (sr == 'FOCUSAREA' ))
        //this.map.setVisible('region', (sr == 'REGION' ))

        data.forEach(function(d){
            var value = Math.round(d.value)
            values[d.area] = value;
            maxValue = Math.max(value, maxValue);
            minValue = Math.min(value, minValue);
        })

        var step = (maxValue - minValue) / 10,
            entries = (step > 0) ? utils.range(minValue, maxValue, step): [0],
            colorRange = this.mapColorRange.domain([minValue, maxValue]);

        this.elLegend.innerHTML = '';
        entries.forEach(function(entry){
            var color = colorRange(entry).hex(),
                square = document.createElement('div'),
                label = document.createElement('label');
            square.style.height = '25px';
            square.style.width = '50px';
            square.style.float = 'left';
            square.style.backgroundColor = color;
            square.style.marginRight = '5px';
            label.innerHTML = _this.format(Math.round(entry)) + ' ' + unit;
            _this.elLegend.appendChild(square);
            _this.elLegend.appendChild(label);
            _this.elLegend.appendChild(document.createElement('br'));
        })
        this.map.addLayer(
            'areas',
            {
                stroke: 'grey',
                strokeWidth: 1,
                colorRange: colorRange,
                //alphaFill: 0.8
            }
        );
        areas.forEach(function(area){
            var coords = area.get('geometry').coordinates,
                name = area.get('name'),
                value = values[area.id],
                fValue = _this.format(value);
            _this.map.addPolygon(coords, {
                projection: 'EPSG:4326', layername: 'areas',
                type: 'MultiPolygon', tooltip: name + ': ' + fValue + ' ' + unit,
                label: fValue + ' ' + unit, id: area.id,
                value: value
            });
        })
        this.map.centerOnLayer('areas');
    },

    saveSession: function(){
        var orderedSelects = this.getOrderedSelects();
        config.session.save({areaSelects: orderedSelects});
    },

    getOrderedSelects: function(){
        var items = this.areaSelectGrid.getItems(),
            orderedSelects = [],
            _this = this;
        items.forEach(function(item){
            var id = item.getElement().dataset['id'];
            // Focus Area has id 0, skip it
            if (id > 0){
                var areaSelect = Object.assign({}, _this.areaSelects[id]);
                areaSelect.id = id;
                orderedSelects.push(areaSelect);
            }
        });
        return orderedSelects;
    },

    restoreSession: function(){
        var orderedSelects = config.session.get('areaSelects'),
            _this = this;
        this.areaSelects = {};
        if (!orderedSelects || orderedSelects.length == 0) return;
        orderedSelects.forEach(function(areaSelect){
            var id = areaSelect.id;
            areaSelect.color = _this.barChartColor(id);
            _this.areaSelects[id] = areaSelect;
            _this.areaSelectIdCnt = Math.max(_this.areaSelectIdCnt, parseInt(id) + 1);
            if(_this.areaSelectRow.querySelector('div.item[data-id="' + id + '"]') == null){
                _this.renderAreaBox(_this.areaSelectRow, id, areaSelect.name, { color: areaSelect.color, fontSize: areaSelect.fontSize });
            }
            var button = _this.el.querySelector('button.select-area[data-id="' + id + '"]'),
                areas = areaSelect.areas;
            if (areas.length > 0){
                button.classList.remove('btn-warning');
                button.classList.add('btn-primary');
            } else {
                button.classList.add('btn-warning');
                button.classList.remove('btn-primary');
            }
        });
        this.addBarChartData(orderedSelects);
    },

    // render item for area selection
    renderAreaBox: function(el, id, title, options){
        var html = document.getElementById('row-box-template').innerHTML,
            template = _.template(html),
            div = document.createElement('div'),
            options = options || {},
            color = options.color || 'grey';
        div.innerHTML = template({
            title: title,
            fontSize: options.fontSize || '60px',
            id: id,
            color: color
        });
        div.classList.add('item');
        el.appendChild(div);
        div.dataset['id'] = id;
        this.areaSelectGrid.add(div);

        return div;
    },

    // render item for bar chart
    renderBarChart: function(){
        var el = this.barChart;
        var div = document.createElement('div');
        el.appendChild(div);
        // user defined areas
        var barChartTab = this.el.querySelector('#bar-charts-tab');
        this.chartLoader = new utils.Loader(barChartTab, {disable: true});
        var width = $("#bar-chart").width();

        //create bar chart
        this.chart = highcharts.chart(div, {
            chart: {
                type: 'column',
                width: 0.85 * width
            },
            tooltip: {
                formatter: function () {
                    return '<b>' + highcharts.numberFormat(this.y, 0, ',', '') + '</b>';
                }
            },
            xAxis: {
                minorTickLength: 0,
                tickLength: 0
            },
            yAxis: {
                min: 0
            },
            title: '',
            legend: {
                enabled: false
            },
            series: [{
                colorByPoint: true,
                data: []
            }]
        });
    },

    // add/overwrite data of single item
    addBarChartItem: function(item){
        var id = item.id,
            areas = item.areas,
            _this = this,
            indicator = this.indicators.get(this.indicatorId);

        if (!indicator) return;

        if (areas.length > 0){
            // compute and return promise
            return indicator.compute({
                method: "POST",
                data: { areas: areas.join(',') },
                success: function(data){
                    var sum = data.reduce((a, b) => a + b.value, 0);
                    _this.chartData[indicator.id][id] = {
                        name: id,
                        value: sum,
                        color: item.color
                    };
                },
                error: _this.onError
            })
        }
        else{
            this.chartData[indicator.id][id] = {
                name: id,
                value: 0
            };
            // no promise to return
        }
    },

    // add data to bar chart
    addBarChartData: function(orderedSelects){
        var _this = this,
            promises = [];
        if(this.indicatorId == -1) return;

        // focus area or case study region
        var indicator = this.indicators.get(this.indicatorId),
            spatialRef = indicator.get('spatial_reference'),
            geom = (spatialRef == 'REGION') ? this.caseStudy.get('geom') : this.caseStudy.get('properties').focusarea,
            text = (spatialRef == 'REGION') ? gettext('Case Study <br> Region') : gettext('Focus <br> Area'),
            fontSize = (spatialRef == 'REGION') ? '30px' : '40px',
            indicatorId = _this.indicatorId;

        var spatialItem = _this.areaSelectRow.querySelector('div.item[data-id="0"]'),
            // ToDo: query by class (did not change the template yet to avoid git conflicts)
            label = spatialItem.querySelector('.item-content>p');
        label.style.fontSize = fontSize;
        label.innerHTML = text;

        promises.push(
            indicator.compute({
                method: "POST",
                data: { geom: JSON.stringify(geom) },
                success: function(data){
                    value = data[0].value;
                    // always prepend focus area
                    _this.chartData[indicatorId][0] = {
                        name: text,
                        value: value
                    };
                },
                error: _this.onError
            })
        )

        if (orderedSelects !== undefined && orderedSelects.length > 0) {
            this.chartLoader.activate();
            orderedSelects.forEach(function(areaSelect){
                var item = _this.areaSelects[areaSelect.id]
                promises.push(_this.addBarChartItem(item))
            });
        }

        $.when.apply($, promises).then(function() {
            _this.updateBarChart();
            _this.chartLoader.deactivate();
        }).catch(function(err) {
            _this.chartLoader.deactivate();
            _this.onError;
        });
    },

    updateBarChart: function(){
        var categories = [],
            data = [],
            chartData = this.chartData[this.indicatorId],
            orderedSelects = this.getOrderedSelects();
        if (!chartData) return;
        if (this.showSpatialItem) {
            // focus area is fixed on pos 0, render first
            var focusData = chartData[0];
            categories.push(focusData.name);
            data.push({
                color: this.spatialItemColor,
                y: focusData.value
            });
        };
        // keep order of user defined area selects
        orderedSelects.forEach(function(areaSelect){
            var id = areaSelect.id,
                d = chartData[id];
            if (!d) return;
            categories.push(areaSelect.name);
            data.push({
                color: d.color,
                y: d.value
            });
        })
        this.chart.xAxis[0].setCategories(categories);
        this.chart.series[0].update({
            data: data
        });
    },

    // render an item where the user can setup areas to be shown as bar charts
    addAreaSelectItem: function(){
        var id = this.areaSelectIdCnt,
            title = id,
            // ToDo: another coloring function
            color = this.barChartColor(id);
        this.renderAreaBox(
            this.areaSelectRow, id, title, { color: color });
        var item = {
            id: id,
            name: title,
            areas: [],
            level: this.areaLevels.first().id,
            color: color
        };
        this.areaSelects[id] = item;
        this.areaSelectIdCnt += 1;
        this.saveSession();
        return item;
    },

    onAddAreaSelect: function(evt){
        var item = this.addAreaSelectItem();
        // fetch and redraw Bar Chart information
        this.addBarChartItem(item);
        this.updateBarChart();
    },

    // item for focus area
    addSpatialItem: function(){
        var div = this.renderAreaBox(
                this.areaSelectRow, 0,
                gettext('Region'),
                {
                    fontSize: '40px',
                    color: this.spatialItemColor
                }
            ),
            buttons = div.querySelectorAll('button'),
            content = div.querySelector('.item-content');
            _this = this;
        for(var i = 0; i < buttons.length; i++)
            buttons[i].style.display = 'none';
        content.classList.remove('shaded');
        function toggleSpatialItem(){
            _this.showSpatialItem = !_this.showSpatialItem;
            content.style.opacity = (_this.showSpatialItem) ? 1 : 0.7;
            content.style.backgroundColor = (_this.showSpatialItem) ? 'white' : '#eaeaea';
            _this.updateBarChart();
        }
        div.addEventListener('click', toggleSpatialItem);
    },

    // remove an area item
    removeAreaSelectItem: function(evt){
        var id = evt.target.dataset['id'],
            div = this.areaSelectRow.querySelector('div.item[data-id="' + id + '"]');
        delete this.areaSelects[id];
        this.areaSelectGrid.remove(div, { removeElements: true });

        //remove bar chart data with it
        var data = this.chartData[this.indicatorId];
        if (data && data[id]) delete data[id];

        this.saveSession();
        this.updateBarChart();
    },

    // initialize the chlorpleth map
    initIndicatorMap: function(){
        var _this = this;
        this.map = new Map({
            el: document.getElementById('indicator-map')
        });
        var focusarea = this.caseStudy.get('properties').focusarea,
            region = this.caseStudy.get('geometry');

        var options = {
            stroke: '#aad400',
            fill: 'rgba(170, 212, 0, 0.1)',
            strokeWidth: 1,
            zIndex: 1
        }
        this.map.addLayer('focusarea', options);
        this.map.addLayer('region', options);

        if(focusarea){
            this.map.addPolygon(focusarea.coordinates, {
                layername: 'focusarea',
                type: 'MultiPolygon',
                label: gettext('Focus Area'),
                tooltip: gettext('Focus Area'),
                projection: this.projection
            })
            this.map.centerOnLayer('focusarea');
            this.map.setVisible('focusarea', false);
        }
        if(region){
            this.map.addPolygon(region.get('coordinates'), {
                layername: 'region',
                type: 'Multipolygon',
                label: gettext('Casestudy Region'),
                tooltip: gettext('Casestudy Region'),
                projection: this.projection
            })
            this.map.centerOnLayer('region');
            this.map.setVisible('region', false);
        }
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
        var id = this.activeAreaSelectId,
            item = this.areaSelects[id],
            _this = this;
        item.areas = this.selectedAreas;
        item.level = this.areaLevelSelect.value;

        var area = this.areas[item.level].get(item.areas[0]);
        var label = area.get('name');
        var count = item.areas.length-1;
        if(count > 0){
            label = label + ' + ' + count;
        }
        this.areaSelects[id].name = label;
        this.areaSelects[id].color = this.barChartColor(id);
        div = this.areaSelectRow.querySelector('div.item[data-id="' + id + '"]');
        var html = document.getElementById('row-box-template').innerHTML,
            template = _.template(html),
            color = this.barChartColor(id);
        div.innerHTML = template({
            title: this.areaSelects[id].name,
            fontSize: '40px',
            id: id,
            color: this.areaSelects[id].color
        });
        // dynamically set font size
        var child = div.children[0];
        var el = child.querySelector("#name");
        var fontSize = parseInt(el.style.fontSize);
        for (var i = fontSize; i >= 0; i--) {
            if (el.scrollHeight > el.clientHeight + 2 || el.scrollWidth > el.clientWidth + 2) {
             fontSize--;
             el.style.fontSize = fontSize + "px";
            }
        }
        this.areaSelects[id].fontSize = fontSize + "px";
        var button = this.el.querySelector('button.select-area[data-id="' + id + '"]')
        if (this.selectedAreas.length > 0){
            button.classList.remove('btn-warning');
            button.classList.add('btn-primary');
        } else {
            button.classList.add('btn-warning');
            button.classList.remove('btn-primary');
        }
        this.saveSession();
        // fetch and redraw Bar Chart information
        this.chartLoader.activate();
        function update(){
            _this.updateBarChart();
            _this.chartLoader.deactivate();
        }
        var promise = this.addBarChartItem(item);
        if (promise)
            promise.then(update);
        else update()
    }
});
return FlowAssessmentWorkshopView;
}
);
