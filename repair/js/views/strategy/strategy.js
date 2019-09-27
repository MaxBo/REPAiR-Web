define(['views/common/baseview', 'underscore', 'collections/gdsecollection/',
        'collections/geolocations/','views/study-area/workshop-maps',
        'visualizations/map', 'utils/utils', 'muuri', 'openlayers',
        'app-config', 'bootstrap', 'bootstrap-select'],

function(BaseView, _, GDSECollection, GeoLocations, BaseMapView, Map, utils,
         Muuri, ol, config){
/**
*
* @author Christoph Franke
* @name module:views/StrategyView
* @augments BaseView
*/
var StrategyView = BaseView.extend(
    /** @lends module:views/StrategyView.prototype */
    {

    /**
    * render workshop view on strategies
    *
    * @param {Object} options
    * @param {HTMLElement} options.el                          element the view will be rendered in
    * @param {string} options.template                         id of the script element containing the underscore template to render this view
    * @param {module:models/CaseStudy} options.caseStudy       the casestudy to add strategies to
    *
    * @constructs
    * @see http://backbonejs.org/#View
    */
    initialize: function(options){
        StrategyView.__super__.initialize.apply(this, [options]);
        _.bindAll(this, 'renderSolution');
        var _this = this;
        this.caseStudy = options.caseStudy;
        this.keyflowName = options.keyflowName;
        this.keyflowId = options.keyflowId;

        this.stakeholderCategories = new GDSECollection([], {
            apiTag: 'stakeholderCategories',
            apiIds: [_this.caseStudy.id]
        });

        this.strategy = options.strategy;

        this.solutionCategories = new GDSECollection([], {
            apiTag: 'solutionCategories',
            apiIds: [this.caseStudy.id, this.keyflowId]
        })

        this.solutions = new GDSECollection([], {
            apiTag: 'solutions',
            apiIds: [this.caseStudy.id, this.keyflowId],
            comparator: 'name'
        });

        var focusarea = this.caseStudy.get('properties').focusarea;
        if (focusarea != null){
            this.focusPoly = new ol.geom.Polygon(focusarea.coordinates[0]);
        }
        this.activityCache = {}

        this.stakeholders = [];
        this.projection = 'EPSG:4326';

        var promises = [
            this.stakeholderCategories.fetch(),
            this.solutionCategories.fetch(),
            this.solutions.fetch()
        ]
        this.loader.activate();
        Promise.all(promises).then(function(){
            var deferreds = [];
            // fetch all stakeholders after fetching their categories
            _this.stakeholderCategories.forEach(function(category){
                var stakeholders = new GDSECollection([], {
                    apiTag: 'stakeholders',
                    apiIds: [_this.caseStudy.id, category.id ]
                });
                category.stakeholders = stakeholders;
                deferreds.push(stakeholders.fetch({ error: _this.onError }))
            });

            _this.solutions.forEach(function(solution){
                solution.questions = new GDSECollection([], {
                    apiTag: 'questions',
                    apiIds: [_this.caseStudy.id, _this.keyflowId, solution.id]
                });
                solution.areas = new GDSECollection([], {
                    apiTag: 'possibleImplementationAreas',
                    apiIds: [_this.caseStudy.id, _this.keyflowId, solution.id]
                });
                deferreds.push(solution.areas.fetch());
                deferreds.push(solution.questions.fetch());
                solution.parts = new GDSECollection([], {
                    apiTag: 'solutionparts',
                    apiIds: [_this.caseStudy.id, _this.keyflowId, solution.id]
                });
                deferreds.push(solution.parts.fetch());
            })
            Promise.all(deferreds).then(_this.render);
        })
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'click #add-solution-strategy-btn': 'addSolution',
        'click #add-solution-modal .confirm': 'confirmNewSolution'
    },

    /*
    * render the view
    */
    render: function(){
        this.loader.deactivate();
        var html = document.getElementById(this.template).innerHTML,
            template = _.template(html),
            _this = this;

        // append solutions to their categories, easier to work with in template
        _this.solutionCategories.forEach(function(category){
            category.solutions = _this.solutions.filterBy({solution_category: category.id});
        });
        this.el.innerHTML = template({
            stakeholderCategories: this.stakeholderCategories,
            solutionCategories: this.solutionCategories,
            keyflowName: this.keyflowName
        });
        $('#solution-select').selectpicker();

        var addBtn = this.el.querySelector('.add');

        this.solutionsInStrategy = new GDSECollection([], {
            apiTag: 'solutionsInStrategy',
            apiIds: [this.caseStudy.id, this.keyflowId, this.strategy.id],
            comparator: 'priority'
        });

        this.strategyGrid = new Muuri(this.el.querySelector('.solutions'), {
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
            dragStartPredicate: {
                handle: '.handle'
            }
        });

        this.strategyGrid.on('dragEnd', function (item) {
            _this.saveOrder();
        });

        this.solutionsInStrategy.fetch({
            success: function(){
                _this.solutionsInStrategy.sort();
                _this.solutionsInStrategy.forEach(function(solInStrategy){
                    _this.renderSolution(solInStrategy);
                })
            }
        });
    },

    addSolution: function(){
        var addModal = this.el.querySelector('#add-solution-modal');
            solutionSelect = addModal.querySelector('#solution-select');

        solutionSelect.selectedIndex = 0;
        $(solutionSelect).selectpicker('refresh');

        $(addModal).modal('show');
    },

    confirmNewSolution: function(){
        var _this = this,
            addModal = this.el.querySelector('#add-solution-modal');
            solutionId = addModal.querySelector('#solution-select').value;
        var solInStrategy = this.solutionsInStrategy.create(
            {
                solution: solutionId
            },
            {
                wait: true,
                success: function(){
                    $(addModal).modal('hide');
                    var solItem = _this.renderSolution(solInStrategy);
                    _this.saveOrder();
                    _this.editSolution(solInStrategy, solItem);
                },
                error: _this.onError
            },
        )
    },

    getStakeholder: function(id){
        var stakeholder = null;
        for (var i = 0; i < this.stakeholderCategories.length; i++){
            stakeholder = this.stakeholderCategories.at(i).stakeholders.get(id);
            if (stakeholder != null) break;
        }
        return stakeholder
    },

    /*
    * render a solution item into the given strategy item
    */
    renderSolution: function(solutionInStrategy){
        var html = document.getElementById('solution-item-template').innerHTML,
            el = document.createElement('div'),
            template = _.template(html),
            solId = solutionInStrategy.get('solution'),
            _this = this;

        var solution = this.solutions.get(solId),
            stakeholderIds = solutionInStrategy.get('participants'),
            stakeholderNames = [];

        // workaround: remove artifact solutions in strategy
        // ToDo: check where those come from
        if (!solution) {
            solutionInStrategy.destroy();
            return;
        };

        stakeholderIds.forEach(function(id){
            var stakeholder = _this.getStakeholder(id);
            stakeholderNames.push(stakeholder.get('name'));
        })

        el.innerHTML = template({
            solutionInStrategy: solutionInStrategy,
            solution: solution,
            stakeholderNames: stakeholderNames.join(', ')
        });
        el.dataset['id'] = solutionInStrategy.id;

        var editBtn = el.querySelector('.edit'),
            removeBtn = el.querySelector('.remove');

        editBtn.addEventListener('click', function(){
            _this.editSolution(solutionInStrategy, el);
        })
        el.classList.add('item', 'large');
        this.strategyGrid.add(el, {});
        removeBtn.addEventListener('click', function(){
            var message = gettext('Do you really want to delete your solution?');
            _this.confirm({ message: message, onConfirm: function(){
                solutionInStrategy.destroy({
                    success: function() { _this.strategyGrid.remove(el, { removeElements: true }); },
                    error: _this.onError,
                    wait: true
                })
            }});
        })
        this.renderSolutionPreviewMap(solutionInStrategy, el);
        return el;
    },


    /*
    * open the modal for editing the solution in strategy
    */
    editSolution: function(solutionImpl, item){
        var _this = this;
        this.selectedActors = {}
        var html = document.getElementById('view-solution-strategy-template').innerHTML,
            template = _.template(html);
        this.solutionModal = this.el.querySelector('#solution-strategy-modal');

        var solId = solutionImpl.get('solution'),
            solution = this.solutions.get(solId);
        this.solutionModal.innerHTML = template({
            solutionCategories: this.solutionCategories,
            solutionImpl: solutionImpl,
            solution: solution,
            stakeholderCategories: this.stakeholderCategories,
            questions: solution.questions,
            solutionparts: solution.parts,
            implementationAreas: solution.areas
        });

        this.drawings = {};

        this.areaSelect = this.solutionModal.querySelector('select[name="implementation-areas"]');
        this.areaSelect.addEventListener('change', function(){
            _this.setupArea(solutionImpl);
            _this.mapEl.classList.remove('disabled');
        });

        var stakeholderSelect = this.solutionModal.querySelector('#strategy-stakeholders'),
            stakeholders = solutionImpl.get('participants').map(String);
        for (var i = 0; i < stakeholderSelect.options.length; i++) {
            if (stakeholders.indexOf(stakeholderSelect.options[i].value) >= 0) {
                stakeholderSelect.options[i].selected = true;
            }
        }
        $(stakeholderSelect).selectpicker();
        this.mapEl = document.getElementById('editor-map');
        if (this.editorMapView) this.editorMapView.close();
        this.editorMapView = new BaseMapView({
            template: 'base-maps-template',
            el: this.mapEl,
            caseStudy: this.caseStudy,
            onReady: function(){
                _this.setupEditor(solutionImpl);
                _this.areaSelect.parentElement.classList.remove('disabled');
                _this.mapEl.classList.add('disabled');
            }
        });

        var actorsLi = this.solutionModal.querySelector('a[href="#actors-tab"]'),
            editorLi = this.solutionModal.querySelector('a[href="#strategy-area-tab"]');
        // update map after switching to tab to fit width and height of wrapping div
        $(editorLi).on('shown.bs.tab', function () {
            if (_this.editorMap) _this.editorMap.map.updateSize();
        });

        $(this.solutionModal).modal('show');

        // save solution and drawn polygons after user confirmed modal
        var okBtn = this.solutionModal.querySelector('.confirm');
        okBtn.addEventListener('click', function(){
            // stakeholders
            var stakeholderIds = [];
            for (var i = 0; i < stakeholderSelect.options.length; i++) {
                var option = stakeholderSelect.options[i];
                if (option.selected) {
                    stakeholderIds.push(option.value);
                }
            }
            solutionImpl.set('participants', stakeholderIds);
            // drawn features
            var areas = []
            for (var areaId in _this.drawings){
                var features = _this.drawings[areaId],
                    geoJSONText = null;
                if (features.length > 0){
                    var multi = new ol.geom.MultiPolygon();
                    features.forEach(function(feature) {
                        var geom = feature.getGeometry().transform(_this.editorMap.mapProjection, _this.projection);
                        if (geom.getType() == 'MultiPolygon'){
                            geom.getPolygons().forEach(function(poly){
                                multi.appendPolygon(poly);
                            })
                        } else {
                            multi.appendPolygon(geom);
                        }
                    });
                    var geoJSON = new ol.format.GeoJSON(),
                        geoJSONText = geoJSON.writeGeometry(multi);
                }
                var implArea = {
                    geom: geoJSONText,
                    possible_implementation_area: areaId
                }
                areas.push(implArea)
            }

            solutionImpl.set('areas', areas);

            var quantityInputs = _this.solutionModal.querySelectorAll('input[name="quantity"]'),
                quantities = [];
            quantityInputs.forEach(function(input){
                var quantity = {
                    question: input.dataset.id,
                    value: input.value
                }
                quantities.push(quantity);
            })

            solutionImpl.set('quantities', quantities);

            var notes = _this.solutionModal.querySelector('textarea[name="description"]').value;
            solutionImpl.set('note', notes);
            solutionImpl.save(null, {
                error: _this.onError,
                patch: true,
                wait: true,
                success: function(){
                    _this.renderSolutionPreviewMap(solutionImpl, item);
                    item.querySelector('textarea[name="notes"]').value = notes;
                    var stakeholderNames = [];
                    stakeholderIds.forEach(function(id){
                        var stakeholder = _this.getStakeholder(id);
                        stakeholderNames.push(stakeholder.get('name'));
                    })
                    item.querySelector('.implemented-by').innerHTML = stakeholderNames.join(', ');
                    $(_this.solutionModal).modal('hide');
                }
            })
        })
    },

    /*
    * render the map with the drawn polygons into the solution item
    */
    renderSolutionPreviewMap: function(solutionImpl, item){
        var divid = 'solutionImpl' + solutionImpl.id,
            _this = this,
            areas = solutionImpl.get('areas');
        var mapDiv = item.querySelector('.olmap');
        mapDiv.id = divid;
        mapDiv.innerHTML = '';
        previewMap = new Map({
            el: document.getElementById(divid),
            enableZoom: false,
            showControls: false,
            enableDrag: false
        });
        var geometries = [];
        areas.forEach(function(area){
            if (!area.geom) return;
            geometries.push(area.geom)
        })
        if (geometries.length > 0){
            previewMap.addLayer('geometry');
            geometries.forEach(function(geom){
                previewMap.addGeometry(geom.coordinates, {
                    projection: _this.projection,
                    layername: 'geometry',
                    type: geom.type
                });
            })
            previewMap.centerOnLayer('geometry');
        }
        else if (this.focusPoly){
            previewMap.centerOnPolygon(this.focusPoly, { projection: this.projection });
        }
    },

    /*
    * render the map to draw on inside the solution modal
    */
    setupEditor: function(solutionImpl){
        var _this = this,
            solution = this.solutions.get(solutionImpl.get('solution')),
            html = document.getElementById('drawing-tools-template').innerHTML,
            template = _.template(html),
            toolsDiv = document.createElement('div');

        toolsDiv.innerHTML = template();
        this.el.querySelector('#base-map').prepend(toolsDiv);

        this.drawingTools = this.el.querySelector('.drawing-tools');
        this.drawingTools.style.visibility = 'hidden';

        this.editorMap = this.editorMapView.map;

        if (this.focusPoly){
            this.editorMap.centerOnPolygon(this.focusPoly, { projection: this.projection });
        };

        this.editorMap.addLayer('mask', {
            stroke: 'grey',
            fill: 'rgba(70, 70, 70, 0.5)',
            strokeWidth: 1,
            zIndex: 999
        });
        this.editorMap.addLayer('implementation-area', {
            stroke: '#aad400',
            fill: 'rgba(170, 212, 0, 0)',
            strokeWidth: 1,
            zIndex: 998
        });

        this.editorMap.addLayer('drawing', {
            select: { selectable: true },
            strokeWidth: 3,
            zIndex: 1000
        });

        this.activityNames = [];

        var removeBtn = this.drawingTools.querySelector('.remove'),
            tools = this.drawingTools.querySelectorAll('.tool'),
            togglePossibleArea = this.el.querySelector('input[name="show-possible-area"]');

        togglePossibleArea.addEventListener('change', function(){
            _this.editorMap.setVisible('implementation-area', this.checked);
            _this.editorMap.setVisible('mask', this.checked);
        })

        function onDrawing(){
            var areaId = _this.areaSelect.value;
            _this.drawings[areaId] = _this.editorMap.getFeatures('drawing');
        }

        removeBtn.addEventListener('click', function(){
            _this.editorMap.removeSelectedFeatures('drawing');
            onDrawing();
        })

        function toolChanged(){
            var checkedTool = _this.drawingTools.querySelector('.active').querySelector('input'),
                type = checkedTool.dataset.tool,
                selectable = false,
                useDragBox = false,
                removeActive = false,
                freehand = checkedTool.dataset.freehand === 'true';
            if (type === 'Move'){
                _this.editorMap.toggleDrawing('drawing');
            }
            else if (type === 'Select'){ // || type === 'DragBox'){
                _this.editorMap.toggleDrawing('drawing');
                selectable = true;
                useDragBox = true;
                removeActive = true;
            }
            else {
                _this.editorMap.toggleDrawing('drawing', {
                    type: type,
                    freehand: freehand,
                    intersectionLayer: 'implementation-area',
                    onDrawEnd: onDrawing
                });
                _this.editorMap.enableDragBox('drawing');
            }
            _this.editorMap.enableSelect('drawing', selectable);
            _this.editorMap.enableDragBox('drawing', useDragBox);
            removeBtn.style.display = (removeActive) ? 'block' : 'none';
        }
        // "Move" tool is selected initially, deactivate selection
        _this.editorMap.enableSelect('drawing', false);

        for (var i = 0; i < tools.length; i++){
            var tool = tools[i];
            // pure js doesn't work unfortunately
            //tool.addEventListener('change', toolChanged);
            $(tool).on('change', toolChanged)
        }
    },

    setupArea: function(solutionImpl){
        var _this = this;
        this.drawingTools.style.visibility = 'visible';
        this.editorMap.clearLayer('mask');
        this.editorMap.clearLayer('implementation-area');
        this.editorMap.clearLayer('drawing');

        this.activityNames.forEach(function(name){
            _this.editorMap.removeLayer('actors' + name);
            _this.removeFromLegend(name);
        });
        this.activityNames = [];

        var solution = this.solutions.get(solutionImpl.get('solution')),
            areaId = this.areaSelect.value;
            possImplArea = solution.areas.get(areaId),
            implAreas = solutionImpl.get('areas'),
            implArea = implAreas.find(function(area){
                return area.possible_implementation_area == areaId;
            });
        var mask = possImplArea.get('edit_mask'),
            maskArea = this.editorMap.addPolygon(mask.coordinates, {
                projection: this.projection,
                layername: 'mask',
                type: mask.type
            });
        var geom = possImplArea.get('geom');
        var area = this.editorMap.addPolygon(geom.coordinates, {
                projection: this.projection,
                layername: 'implementation-area',
                type: geom.type
                //tooltip: gettext('possible implementation area')
            });
        this.editorMap.centerOnPolygon(area, { projection: this.projection });

        if (implArea && implArea.geom){
            _this.editorMap.addGeometry(implArea.geom.coordinates, {
                projection: _this.projection, layername: 'drawing',
                type: implArea.geom.type
            });
            _this.editorMap.centerOnLayer('drawing');
        }

        var actorIds = possImplArea.get('affected_actors');
        var actors = new GDSECollection([], {
            apiTag: 'actors',
            apiIds: [this.caseStudy.id, this.keyflowId]
        });
        var locations = new GeoLocations([], {
            apiTag: 'adminLocations',
            apiIds: [this.caseStudy.id, this.keyflowId]
        });
        var promises = [];
        if (actorIds.length > 0){
            this.loader.activate();
            promises.push(actors.postfetch({
                body: {id: actorIds.join(',')},
                error: _this.onError
            }));
            promises.push(locations.postfetch({
                body: {actor__in: actorIds.join(',')},
                error: _this.onError
            }));
        }

        function bgColor(color){
            if(color.length < 5) {
                color += color.slice(1);
            }
            return (color.replace('#','0x')) > (0xffffff/2) ? '#333' : '#fff';
        };

        Promise.all(promises).then(function(){
            var activityNames = [...new Set(actors.pluck('activity_name'))];
            activityNames.forEach(function(activityName){
                var color = utils.colorByName(activityName),
                    layername = 'actors' + activityName;
                _this.editorMap.addLayer(layername, {
                    stroke: 'black',
                    fill: color,
                    labelColor: color,
                    labelOutline: bgColor(color),
                    labelFontSize: '12px',
                    labelOffset: 15,
                    strokeWidth: 1,
                    zIndex: 1001
                });
                _this.addToLegend(activityName, color);
                _this.activityNames.push(activityName);
            })
            locations.forEach(function(location){
                var geom = location.get('geometry'),
                    actor = actors.get(location.get('properties').actor),
                    activityName = actor.get('activity_name');
                if (!geom && !geom.get('coordinates')) return;
                _this.editorMap.addGeometry(geom.get('coordinates'), {
                    projection: _this.projection,
                    tooltip: actor.get('name'),
                    layername: 'actors' + activityName,
                    label: actor.get('name'),
                    type: 'Point'
                });
            })
            _this.loader.deactivate();
        })
    },

    saveOrder: function(){
        var items = this.strategyGrid.getItems(),
            i = 0,
            _this = this;
        items.forEach(function(item){
            var id = item.getElement().dataset['id'];
            _this.solutionsInStrategy.get(id).save({ priority: i }, { patch: true })
            i++;
        });
    },

    addToLegend: function(activityName, color){
        var legend = this.el.querySelector('#legend'),
            itemsDiv = legend.querySelector('.items'),
            legendDiv = document.createElement('div'),
            circle = document.createElement('div'),
            textDiv = document.createElement('div'),
            head = document.createElement('b'),
            img = document.createElement('img');
        legendDiv.dataset['activity'] = activityName;
        textDiv.innerHTML = gettext('actors') + ' ' + activityName;
        textDiv.style.overflow = 'hidden';
        textDiv.style.textOverflow = 'ellipsis';
        legendDiv.appendChild(circle);
        legendDiv.appendChild(textDiv);
        circle.style.backgroundColor = color;
        circle.style.float = 'left';
        circle.style.width = '20px';
        circle.style.height = '20px';
        circle.style.marginRight = '5px';
        circle.style.borderRadius = '10px';
        legendDiv.style.marginBottom = '10px';
        itemsDiv.prepend(legendDiv);
    },

    removeFromLegend: function(activityName){
        var legend = this.el.querySelector('#legend'),
            itemsDiv = legend.querySelector('.items');
            entry = itemsDiv.querySelector('div[data-activity="' + activityName + '"]');
        itemsDiv.removeChild(entry);
    },

});
return StrategyView;
}
);
