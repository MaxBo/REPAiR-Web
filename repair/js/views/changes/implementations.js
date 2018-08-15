define(['views/baseview', 'underscore', 'collections/gdsecollection/', 
        'visualizations/map', 'utils/utils', 'muuri', 'openlayers', 'bootstrap', 
        'bootstrap-select'],

function(BaseView, _, GDSECollection, Map, utils, Muuri, ol){
/**
*
* @author Christoph Franke
* @name module:views/ImplementationsView
* @augments BaseView
*/
var ImplementationsView = BaseView.extend(
    /** @lends module:views/ImplementationsView.prototype */
    {

    /**
    * render workshop view on implementations
    *
    * @param {Object} options
    * @param {HTMLElement} options.el                          element the view will be rendered in
    * @param {string} options.template                         id of the script element containing the underscore template to render this view
    * @param {module:models/CaseStudy} options.caseStudy       the casestudy to add implementations to
    *
    * @constructs
    * @see http://backbonejs.org/#View
    */
    initialize: function(options){
        ImplementationsView.__super__.initialize.apply(this, [options]);
        _.bindAll(this, 'renderImplementation');
        _.bindAll(this, 'renderSolution');
        var _this = this;
        this.caseStudy = options.caseStudy;
        this.stakeholderCategories = new GDSECollection([], { 
            apiTag: 'stakeholderCategories',
            apiIds: [_this.caseStudy.id]
        });
        
        this.implementations = new GDSECollection([], {
            apiTag: 'implementations', 
            apiIds: [this.caseStudy.id] 
        });
        
        this.units = new GDSECollection([], {
            apiTag: 'units'
        });
        
        this.solutionCategories = new GDSECollection([], {
            apiTag: 'solutionCategories',
            apiIds: [this.caseStudy.id] 
        });
        
        var focusarea = this.caseStudy.get('properties').focusarea;
        if (focusarea != null){
            this.focusPoly = new ol.geom.Polygon(focusarea.coordinates[0]);
        }
        
        this.stakeholders = [];
        this.solutions = [];
        this.projection = 'EPSG:4326';
        
        var promises = [
            this.implementations.fetch(), 
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
                    apiIds: [_this.caseStudy.id, category.id] 
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
        'click #add-implementation': 'addImplementation',
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
            solutionCategories: this.solutionCategories
        });
        $('#coordinator-select').selectpicker();
        $('#solution-select').selectpicker();
        
        this.implementations.forEach(this.renderImplementation);
        
        document.querySelector('#implementation-modal .confirm').addEventListener(
            'click', function(){ _this.confirmImplementation() })
        document.querySelector('#add-solution-modal .confirm').addEventListener(
            'click', function(){ _this.confirmNewSolution() })
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
    * render an implementation item
    */
    renderImplementation: function(implementation){
        var html = document.getElementById('implementation-item-template').innerHTML,
            el = document.createElement('div'),
            template = _.template(html),
            coordId = implementation.get('coordinating_stakeholder'),
            implDiv = this.el.querySelector('#implementations'),
            stakeholder = this.getStakeholder(coordId),
            _this = this;
        
        implDiv.appendChild(el);
        el.innerHTML = template({ implementation: implementation, stakeholder: stakeholder });
        
        var editBtn = el.querySelector('.edit'),
            removeBtn = el.querySelector('.remove'),
            addBtn = el.querySelector('.add');
        
        editBtn.addEventListener('click', function(){
            _this.editImplementation(implementation, el);
        })
        
        removeBtn.addEventListener('click', function(){
            var message = gettext('Do you really want to delete the implementation and all of its solutions?');
            _this.confirm({ message: message, onConfirm: function(){
                implementation.destroy({
                    success: function() { implDiv.removeChild(el); },
                    error: _this.onError,
                    wait: true
                })
            }});
        })
        
        var solutionsInImpl = new GDSECollection([], {
            apiTag: 'solutionsInImplementation', 
            apiIds: [this.caseStudy.id, implementation.id] 
        });
        
        var implementationGrid = new Muuri(el.querySelector('.solutions'), {
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
        
        solutionsInImpl.fetch({
            success: function(){ 
                solutionsInImpl.forEach(function(solInImpl){
                    _this.renderSolution(solInImpl, implementation, implementationGrid);
                })
            }
        });
        
        var addModal = this.el.querySelector('#add-solution-modal');
        addBtn.addEventListener('click', function(){
            _this.confirmNewSolution = function(){
                var solutionId = _this.el.querySelector('#solution-select').value;
                var solInImpl = solutionsInImpl.create(
                    {
                        solution: solutionId
                    }, 
                    { 
                        wait: true,
                        success: function(){
                            $(addModal).modal('hide');
                            var solItem = _this.renderSolution(solInImpl, implementation, implementationGrid);
                            _this.editSolution(solInImpl, implementation, solItem);
                        },
                        error: _this.onError
                    },
                )
            };
            
            var solutionSelect = addModal.querySelector('#solution-select');
            
            solutionSelect.selectedIndex = 0;
            $(solutionSelect).selectpicker('refresh');
            
            $(addModal).modal('show');
        })
    },
    
    /*
    * render a solution item into the given implementation item
    */
    renderSolution: function(solutionInImpl, implementation, grid){
        var html = document.getElementById('solution-item-template').innerHTML,
            el = document.createElement('div'),
            template = _.template(html),
            solId = solutionInImpl.get('solution'),
            _this = this;
        
        var solution;
        for (var i = 0; i < this.solutionCategories.length; i++){
            solution = this.solutionCategories.at(i).solutions.get(solId);
            if (solution != null) break;
        }
        
        var stakeholderIds = solutionInImpl.get('participants'),
            stakeholderNames = [];
        
        stakeholderIds.forEach(function(id){
            var stakeholder = _this.getStakeholder(id);
            stakeholderNames.push(stakeholder.get('name'));
        })
        var quantityLabels = [];
        
        var squantities = new GDSECollection([], {
            apiTag: 'quantitiesInImplementedSolution', 
            apiIds: [this.caseStudy.id, implementation.id, solutionInImpl.id] 
        });
        
        el.innerHTML = template({ 
            solutionInImpl: solutionInImpl, 
            solution: solution, 
            stakeholderNames: stakeholderNames.join(', ')
        });
        
        squantities.fetch({success: function(){
            squantities.forEach(function(quantity){
                quantityLabels.push(quantity.get('value') + ' ' + quantity.get('unit'));
            })
            el.querySelector('.quantity').innerHTML = quantityLabels.join(', ');
        }})
        
        var editBtn = el.querySelector('.edit'),
            removeBtn = el.querySelector('.remove');
        
        editBtn.addEventListener('click', function(){
            _this.editSolution(solutionInImpl, implementation, el);
        })
        el.classList.add('item', 'large');
        grid.add(el, {});
        removeBtn.addEventListener('click', function(){
            var message = gettext('Do you really want to delete your solution?');
            _this.confirm({ message: message, onConfirm: function(){
                solutionInImpl.destroy({
                    success: function() { grid.remove(el, { removeElements: true }); },
                    error: _this.onError,
                    wait: true
                })
            }});
        })
        this.renderSolutionPreviewMap(solutionInImpl, el);
        return el;
    },
    
    /*
    * open modal for editing an implementation
    */
    editImplementation: function(implementation, item){
        var modal = this.el.querySelector('#implementation-modal'),
            nameInput = modal.querySelector('#implementation-name-input'),
            coordSelect = modal.querySelector('#coordinator-select'),
            _this = this;
        
        nameInput.value = implementation.get('name');
        coordSelect.value = implementation.get('coordinating_stakeholder');
        $(coordSelect).selectpicker('refresh');
        
        this.confirmImplementation = function(){
            implementation.save(
                { 
                    name: nameInput.value, 
                    coordinating_stakeholder: coordSelect.value
                }, 
                {
                    success: function(){
                        item.querySelector('.title').innerHTML = nameInput.value;
                        item.querySelector('.coordinator').innerHTML = coordSelect[coordSelect.selectedIndex].text;
                        $(modal).modal('hide');
                },
                error: _this.onError
            })
        };
        
        $(modal).modal('show');
    },
    
    /*
    * add a implementation and save it
    */
    addImplementation: function(){
        var modal = this.el.querySelector('#implementation-modal'),
            nameInput = modal.querySelector('#implementation-name-input'),
            coordSelect = modal.querySelector('#coordinator-select'),
            _this = this;
        
        nameInput.value = '';
        coordSelect.selectedIndex = 0;
        $(coordSelect).selectpicker('refresh');
        
        this.confirmImplementation = function(){
            var implementation = _this.implementations.create(
                {
                    name: nameInput.value,
                    coordinating_stakeholder: coordSelect.value
                }, 
                { 
                    wait: true,
                    success: function(){
                        _this.renderImplementation(implementation);
                        $(modal).modal('hide');
                    },
                    error: _this.onError
                },
            )
        };
        
        $(modal).modal('show');
    },
    
    /*
    * open the modal for editing the solution in implementation
    */
    editSolution: function(solutionImpl, implementation, item){
        var _this = this;
        var html = document.getElementById('view-solution-implementation-template').innerHTML,
            template = _.template(html);
        var modal = this.el.querySelector('#solution-implementation-modal');
        
        var solution = null,
            solId = solutionImpl.get('solution');
        
        for (var i = 0; i < this.solutionCategories.length; i++){
            solution = this.solutionCategories.at(i).solutions.get(solId);
            if (solution != null) break;
        }
        
        modal.innerHTML = template({ 
            solutionCategories: this.solutionCategories,
            implementation: implementation,
            solutionImpl: solutionImpl,
            solution: solution,
            stakeholderCategories: this.stakeholderCategories
        });
        
        var stakeholderSelect = modal.querySelector('#implementation-stakeholders'),
            stakeholders = solutionImpl.get('participants').map(String);
        for (var i = 0; i < stakeholderSelect.options.length; i++) {
            if (stakeholders.indexOf(stakeholderSelect.options[i].value) >= 0) {
                stakeholderSelect.options[i].selected = true;
            }
        }
        $(stakeholderSelect).selectpicker();
        
        var squantities = new GDSECollection([], {
            apiTag: 'quantitiesInImplementedSolution', 
            apiIds: [this.caseStudy.id, implementation.id, solutionImpl.id] 
        });

        var sratios = new GDSECollection([], {
            apiTag: 'solutionRatioOneUnits', 
            apiIds: [this.caseStudy.id, solution.get('solution_category'), solution.id] 
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
        var mapDiv = item.querySelector('.map');
        mapDiv.id = divid;
        mapDiv.innerHTML = '';
        previewMap = new Map({
            el: document.getElementById(divid), 
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

});
return ImplementationsView;
}
);
