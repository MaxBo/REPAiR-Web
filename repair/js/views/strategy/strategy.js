define(['views/common/baseview', 'underscore', 'collections/gdsecollection/',
        'visualizations/map', 'utils/utils', 'muuri', 'openlayers',
        'app-config', 'bootstrap', 'bootstrap-select'],

function(BaseView, _, GDSECollection, Map, utils, Muuri, ol, config){
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

        this.strategies = new GDSECollection([], {
            apiTag: 'strategies',
            apiIds: [this.caseStudy.id, this.keyflowId]
        });

        this.units = new GDSECollection([], {
            apiTag: 'units'
        });

        // ToDo: replace with collections fetched from server
        this.solutionCategories = new GDSECollection([], {
            apiTag: 'solutionCategories',
            apiIds: [this.caseStudy.id, this.keyflowId]
        })

        var focusarea = this.caseStudy.get('properties').focusarea;
        if (focusarea != null){
            this.focusPoly = new ol.geom.Polygon(focusarea.coordinates[0]);
        }

        this.stakeholders = [];
        this.solutions = [];
        this.projection = 'EPSG:4326';

        var promises = [
            this.strategies.fetch(),
            this.stakeholderCategories.fetch(),
            this.solutionCategories.fetch(),
            this.units.fetch()
        ]

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
            // fetch all solutions after fetching the categories
            _this.solutionCategories.forEach(function(category){
                var solutions = new GDSECollection([], {
                    apiTag: 'solutions',
                    apiIds: [_this.caseStudy.id, _this.keyflowId, category.id]
                });
                category.solutions = solutions;
                deferreds.push(solutions.fetch({ error: _this.onError }))
            });

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
        var html = document.getElementById(this.template).innerHTML,
            template = _.template(html),
            _this = this;
        this.el.innerHTML = template({
            stakeholderCategories: this.stakeholderCategories,
            solutionCategories: this.solutionCategories,
            keyflowName: this.keyflowName
        });
        $('#solution-select').selectpicker();

        // there is only one strategy allowed per user
        this.strategy = this.strategies.first();

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

        var solution;
        for (var i = 0; i < this.solutionCategories.length; i++){
            solution = this.solutionCategories.at(i).solutions.get(solId);
            if (solution != null) break;
        }

        if (!solution) return;

        var stakeholderIds = solutionInStrategy.get('participants'),
            stakeholderNames = [];

        stakeholderIds.forEach(function(id){
            var stakeholder = _this.getStakeholder(id);
            stakeholderNames.push(stakeholder.get('name'));
        })
        var quantityLabels = [];

        var squantities = new GDSECollection([], {
            apiTag: 'quantitiesInImplementedSolution',
            apiIds: [this.caseStudy.id, this.keyflowId, this.strategy.id, solutionInStrategy.id]
        });

        el.innerHTML = template({
            solutionInStrategy: solutionInStrategy,
            solution: solution,
            stakeholderNames: stakeholderNames.join(', ')
        });
        el.dataset['id'] = solutionInStrategy.id;

        squantities.fetch({success: function(){
            squantities.forEach(function(quantity){
                quantityLabels.push(quantity.get('value') + ' ' + quantity.get('unit'));
            })
            el.querySelector('.quantity').innerHTML = quantityLabels.join(', ');
        }})

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
        var html = document.getElementById('view-solution-strategy-template').innerHTML,
            template = _.template(html);
        var modal = this.el.querySelector('#solution-strategy-modal');

        var solution = null,
            solId = solutionImpl.get('solution');

        for (var i = 0; i < this.solutionCategories.length; i++){
            solution = this.solutionCategories.at(i).solutions.get(solId);
            if (solution != null) break;
        }

        modal.innerHTML = template({
            solutionCategories: this.solutionCategories,
            solutionImpl: solutionImpl,
            solution: solution,
            stakeholderCategories: this.stakeholderCategories
        });

        var stakeholderSelect = modal.querySelector('#strategy-stakeholders'),
            stakeholders = solutionImpl.get('participants').map(String);
        for (var i = 0; i < stakeholderSelect.options.length; i++) {
            if (stakeholders.indexOf(stakeholderSelect.options[i].value) >= 0) {
                stakeholderSelect.options[i].selected = true;
            }
        }
        $(stakeholderSelect).selectpicker();

        var squantities = new GDSECollection([], {
            apiTag: 'quantitiesInImplementedSolution',
            apiIds: [this.caseStudy.id, this.keyflowId, this.strategy.id, solutionImpl.id]
        });

        var sratios = new GDSECollection([], {
            apiTag: 'solutionRatioOneUnits',
            apiIds: [this.caseStudy.id, this.keyflowId, solution.get('solution_category'), solution.id]
        });

        var quantityTable = modal.querySelector('#implemented-quantities');
        // render the quantities and ratios (tab "Quantities")
        squantities.fetch({success: function(){
            squantities.forEach(function(quantity){
                var row = quantityTable.insertRow(-1),
                    nameCell = row.insertCell(-1);
                nameCell.innerHTML = quantity.get('name');
                nameCell.style.width= '1%';
                nameCell.style.whiteSpace = 'nowrap';
                var input = document.createElement('input');
                input.type = 'number';
                input.dataset.id = quantity.id;
                input.value = quantity.get('value');
                input.classList.add('form-control');
                var inputCell = row.insertCell(-1);
                inputCell.style.width= '1%';
                inputCell.style.whiteSpace = 'nowrap';
                input.style.width = '200px';
                inputCell.appendChild(input);
                row.insertCell(-1).innerHTML = quantity.get('unit');
            });
        }});
        sratios.fetch({success: function(){
            var div = modal.querySelector('#ratios');
            sratios.forEach(function(ratio){
                var li = document.createElement('li');
                li.innerHTML = ratio.get('name') + ': ' + ratio.get('value') + ' ' + (_this.units.get(ratio.get('unit')).get('name'));
                div.appendChild(li);
            });
        }});

        this.renderEditorMap('editor-map', solutionImpl);
        // update map after modal is rendered to fit width and height of wrapping div
        $(modal).off();
        $(modal).on('shown.bs.modal', function () {
            _this.editorMap.map.updateSize();
        });
        $(modal).modal('show');

        // save solution and drawn polygons after user confirmed modal
        var okBtn = modal.querySelector('.confirm');
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
                    geometries.push(geom)
                });
                var geoCollection = new ol.geom.GeometryCollection(geometries),
                    geoJSON = new ol.format.GeoJSON(),
                    geoJSONText = geoJSON.writeGeometry(geoCollection);
                solutionImpl.set('geom', geoJSONText);
            }
            var notes = modal.querySelector('textarea[name="description"]').value;
            solutionImpl.set('note', notes);
            var promises = [
                solutionImpl.save(null, {
                    error: _this.onError,
                    patch: true,
                    wait: true
                })
            ]
            squantities.forEach(function(quantity){
                var input = quantityTable.querySelector('input[data-id="' + quantity.id + '"]');
                quantity.set('value', input.value);
                promises.push(quantity.save(null, {
                    error: _this.onError,
                    wait: true
                }))
            })
            Promise.all(promises).then(function(){
                _this.renderSolutionPreviewMap(solutionImpl, item);
                item.querySelector('textarea[name="notes"]').value = notes;
                var stakeholderNames = [];
                stakeholderIds.forEach(function(id){
                    var stakeholder = _this.getStakeholder(id);
                    stakeholderNames.push(stakeholder.get('name'));
                })
                var quantityLabels = [];
                squantities.forEach(function(quantity){
                    quantityLabels.push(quantity.get('value') + ' ' + quantity.get('unit'));
                })
                item.querySelector('.quantity').innerHTML = quantityLabels.join(', ');
                item.querySelector('.implemented-by').innerHTML = stakeholderNames.join(', ');
                $(modal).modal('hide');
            })
        })
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
            showControls: false
        });
        var geom = solutionImpl.get('geom');
        if (geom != null){
            previewMap.addLayer('geometry')
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

    /*
    * render the map to draw on inside the solution modal
    */
    renderEditorMap: function(divid, solutionImpl, activities){
        var _this = this,
            el = document.getElementById(divid);
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
            _this.solutionsInStrategy.get(id).save({ priority: i })
            i++;
        });
    }

});
return StrategyView;
}
);
