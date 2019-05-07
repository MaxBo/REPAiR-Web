define(['views/common/baseview', 'underscore', 'collections/gdsecollection/',
        'collections/geolocations/',
        'visualizations/map', 'utils/utils', 'muuri', 'openlayers',
        'app-config', 'bootstrap', 'bootstrap-select'],

function(BaseView, _, GDSECollection, GeoLocations, Map, utils, Muuri, ol, config){
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
            solutionparts: solution.parts
        });

        var stakeholderSelect = this.solutionModal.querySelector('#strategy-stakeholders'),
            stakeholders = solutionImpl.get('participants').map(String);
        for (var i = 0; i < stakeholderSelect.options.length; i++) {
            if (stakeholders.indexOf(stakeholderSelect.options[i].value) >= 0) {
                stakeholderSelect.options[i].selected = true;
            }
        }
        $(stakeholderSelect).selectpicker();

        this.renderEditorMap('editor-map', solutionImpl);

        var hasActorsToPick = false;
        solution.parts.forEach(function(part){
            if (part.get('implements_new_flow')) hasActorsToPick = true;
        })

        var actorsLi = this.solutionModal.querySelector('a[href="#actors-tab"]'),
            editorLi = this.solutionModal.querySelector('a[href="#strategy-area-tab"]');
        // update map after switching to tab to fit width and height of wrapping div
        $(editorLi).on('shown.bs.tab', function () {
            _this.editorMap.map.updateSize();
        });
        if (hasActorsToPick){
            this.pickedActors = {};
            solutionImpl.get('picked_actors').forEach(function(pick){
                _this.pickedActors[pick.solutionpart] = pick.actor;
            })
            this.renderActorMap('actor-map', solutionImpl);
            $(actorsLi).on('shown.bs.tab', function () {
                _this.actorMap.map.updateSize();
            });

            var requestSelect = this.solutionModal.querySelector('select[name="map-request"]');
            requestSelect.addEventListener('change', function(){
                var picked = _this.pickedActors[this.value];
                _this.renderSelectableActors(solution.parts.get(this.value), picked);
            });
        }
        else
            actorsLi.style.display = 'none';

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
            var features = _this.editorMap.getFeatures('drawing');
            if (features.length > 0){
                var geometries = [];
                features.forEach(function(feature) {
                    var geom = feature.getGeometry();
                    geometries.push(geom);
                });
                var geoCollection = new ol.geom.GeometryCollection(geometries),
                    geoJSON = new ol.format.GeoJSON(),
                    geoJSONText = geoJSON.writeGeometry(geoCollection);
                solutionImpl.set('geom', geoJSONText);
            }

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

            if (hasActorsToPick){
                var picked = [];
                for (var partId in _this.pickedActors){
                    picked.push({
                        solutionpart: partId,
                        actor: _this.pickedActors[partId]
                    })
                }
                solutionImpl.set('picked_actors', picked);
            }

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

    // render the administrative locations of all actors of activity in solutionpart
    renderSelectableActors: function(solutionpart, picked){
        var _this = this,
            activityId = solutionpart.get('new_target_activity');
        if (!activityId) return;

        var cache = this.activityCache[activityId];

        function renderActors(actors, locations){
            _this.actorMap.clearLayer('pickable-actors');
            if (cache.actors.length === 0) return;
            cache.locations.forEach(function(loc){
                var properties = loc.get('properties'),
                    actor = cache.actors.get(properties.actor),
                    geom = loc.get('geometry');
                if (geom) {
                    _this.actorMap.addGeometry(geom.get('coordinates'), {
                        projection: _this.projection,
                        layername: 'pickable-actors',
                        tooltip: actor.get('name'),
                        label: actor.get('name'),
                        id: actor.id,
                        type: 'Point'
                    });
                }
            })
            if (picked)
                _this.actorMap.selectFeature('pickable-actors', picked);
        }

        if (!cache){
            this.activityCache[activityId] = cache = {};
            cache.actors = new GDSECollection([], {
                apiTag: 'actors',
                apiIds: [this.caseStudy.id, this.keyflowId]
            })
            cache.actors.fetch({
                data: { activity: activityId, included: "True" },
                processData: true,
                success: function(){
                    if (cache.actors.length === 0) return;
                    var actorIds = cache.actors.pluck('id');
                    cache.locations = new GeoLocations([],{
                        apiTag: 'adminLocations',
                        apiIds: [_this.caseStudy.id, _this.keyflowId]
                    });
                    var data = {};
                    data['actor__in'] = actorIds.toString();
                    cache.locations.fetch({
                        data: data,
                        processData: true,
                        success: function(){
                            renderActors(cache.actors, cache.locations)
                        },
                        error: _this.onError
                    })
                },
                error: _this.onError
            })
        }
        else renderActors(cache.actors, cache.locations);
    },
    /*
    * render the map with the drawn polygons into the solution item
    */
    renderSolutionPreviewMap: function(solutionImpl, item){
        var divid = 'solutionImpl' + solutionImpl.id;
        var mapDiv = item.querySelector('.olmap');
        mapDiv.id = divid;
        mapDiv.innerHTML = '';
        previewMap = new Map({
            el: document.getElementById(divid),
            enableZoom: false,
            showControls: false,
            enableDrag: false
        });
        var geom = solutionImpl.get('geom');
        if (geom != null){
            previewMap.addLayer('geometry');
            geom.geometries.forEach(function(g){
                previewMap.addGeometry(g.coordinates, {
                    projection: 'EPSG:3857', layername: 'geometry',
                    type: g.type
                });
            })
            previewMap.centerOnLayer('geometry');
        }
        else if (this.focusPoly){
            previewMap.centerOnPolygon(this.focusPoly, { projection: this.projection });
        }
    },

    renderActorMap: function(divid, solutionImpl) {
        var el = document.getElementById(divid),
            _this = this;

        // calculate (min) height
        var height = document.body.clientHeight * 0.6;
        el.style.height = height + 'px';
        // remove old map
        if (this.actorMap){
            this.actorMap.map.setTarget(null);
            this.actorMap.map = null;
            this.actorMap = null;
        }
        this.actorMap = new Map({
            el: el
        });

        if (this.focusPoly){
            this.actorMap.centerOnPolygon(this.focusPoly, { projection: this.projection });
        };
        var requestSelect = this.solutionModal.querySelector('select[name="map-request"]');
        this.actorMap.addLayer('pickable-actors', {
            stroke: 'black',
            fill: 'red',
            strokeWidth: 1,
            zIndex: 1,
            icon: '/static/img/map-marker-red.svg',
            anchor: [0.5, 1],
            labelColor: '#111',
            labelOutline: 'white',
            select: {
                selectable: true,
                onChange: function(feature){
                    _this.pickedActors[requestSelect.value] = feature[0].id;
                },
                multi: false,
                icon: '/static/img/map-marker-yellow.svg',
                anchor: [0.5, 1],
                labelColor: 'yellow',
                labelOutline: '#111'
            }
        });
    },

    /*
    * render the map to draw on inside the solution modal
    */
    renderEditorMap: function(divid, solutionImpl){
        var _this = this,
            el = document.getElementById(divid),
            solution = this.solutions.get(solutionImpl.get('solution'));
        // calculate (min) height
        var height = document.body.clientHeight * 0.6;
        el.style.height = height + 'px';
        // remove old map
        if (this.editorMap){
            this.editorMap.map.setTarget(null);
            this.editorMap.map = null;
            this.editorMap = null;
        }
        this.editorMap = new Map({
            el: el
        });

        if (this.focusPoly){
            this.editorMap.centerOnPolygon(this.focusPoly, { projection: this.projection });
        };

        this.editorMap.addLayer('mask', {
            stroke: 'grey',
            fill: 'rgba(70, 70, 70, 0.5)',
            strokeWidth: 1,
            zIndex: 0
        });
        this.editorMap.addLayer('implementation-area', {
            stroke: '#aad400',
            fill: 'rgba(170, 212, 0, 0)',
            strokeWidth: 1,
            zIndex: 0
        });


        var implArea = solution.get('possible_implementation_area') || '';
        if(implArea) {
            var mask = solution.get('edit_mask');
            var maskArea = this.editorMap.addPolygon(mask.coordinates, {
                projection: this.projection,
                layername: 'mask',
                type: mask.type,
                tooltip: gettext('possible implementation area')
            });
            var area = this.editorMap.addPolygon(implArea.coordinates, {
                projection: this.projection,
                layername: 'implementation-area',
                type: implArea.type,
                tooltip: gettext('possible implementation area')
            });
            this.editorMap.centerOnPolygon(area, { projection: this.projection });
        }


        var geom = solutionImpl.get('geom');

        this.editorMap.addLayer('drawing', {
            select: { selectable: true },
            strokeWidth: 3
        });

        if (geom){
            geom.geometries.forEach(function(g){
                _this.editorMap.addGeometry(g.coordinates, {
                    projection: 'EPSG:3857', layername: 'drawing',
                    type: g.type
                });
            })
            _this.editorMap.centerOnLayer('drawing');
        }
        var drawingTools = this.el.querySelector('.drawing-tools'),
            removeBtn = drawingTools.querySelector('.remove'),
            freehand = drawingTools.querySelector('.freehand'),
            tools = drawingTools.querySelectorAll('.tool');

        function toolChanged(){
            var checkedTool = drawingTools.querySelector('.active').querySelector('input'),
                type = checkedTool.dataset.tool,
                selectable = false,
                useDragBox = false,
                removeActive = false;
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
                    freehand: freehand.checked
                });
                _this.editorMap.enableDragBox('drawing');
            }
            // seperate dragbox tool disabled, doesn't work with touch
            //if (type === 'DragBox') useDragBox = true;
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
        freehand.addEventListener('change', toolChanged);

        removeBtn.addEventListener('click', function(){
            _this.editorMap.removeSelectedFeatures('drawing');
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
    }

});
return StrategyView;
}
);
