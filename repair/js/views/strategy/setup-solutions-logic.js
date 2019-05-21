define(['views/common/baseview', 'underscore', 'collections/gdsecollection',
        'models/gdsemodel', 'views/strategy/setup-solution-part', 'views/strategy/setup-question',
        'collections/geolocations', 'visualizations/map', 'viewerjs', 'app-config',
        'utils/utils', 'muuri', 'visualizations/map',
        'bootstrap', 'viewerjs/dist/viewer.css', 'bootstrap-select'],

function(BaseView, _, GDSECollection, GDSEModel, SolutionPartView, QuestionView,
         GeoLocations, Map, Viewer, config, utils, Muuri, Map){
/**
*
* @author Christoph Franke
* @name module:views/SolutionsLogicView
* @augments BaseView
*/
var SolutionsLogicView = BaseView.extend(
    /** @lends module:views/SolutionsLogicView.prototype */
    {

    /**
    * render setup and workshop view on solutions
    *
    * @param {Object} options
    * @param {HTMLElement} options.el                          element the view will be rendered in
    * @param {string} options.template                         id of the script element containing the underscore template to render this view
    * @param {module:models/CaseStudy} options.caseStudy       the casestudy to add solutions to
    *
    * @constructs
    * @see http://backbonejs.org/#View
    */
    initialize: function(options){
        SolutionsLogicView.__super__.initialize.apply(this, [options]);
        var _this = this;
        _.bindAll(this, 'editItem');
        _.bindAll(this, 'uploadPriorities');
        _.bindAll(this, 'renderSolution');

        this.template = options.template;
        this.caseStudy = options.caseStudy;
        this.keyflowId = options.keyflowId;

        this.solutions = options.solutions;
        this.categories = options.categories;

        this.materials = new GDSECollection([], {
            apiTag: 'materials',
            apiIds: [this.caseStudy.id, this.keyflowId],
            comparator: 'level'
        }),
        this.activityGroups = new GDSECollection([], {
            apiTag: 'activitygroups',
            apiIds: [this.caseStudy.id, this.keyflowId],
            comparator: 'name'
        });
        this.activities = new GDSECollection([], {
            apiTag: 'activities',
            apiIds: [this.caseStudy.id, this.keyflowId],
            comparator: 'name'
        });

        var promises = [];
        promises.push(this.activities.fetch());
        promises.push(this.activityGroups.fetch());
        promises.push(this.materials.fetch());

        this.loader.activate();
        Promise.all(promises).then(function(){
            _this.loader.deactivate();
            _this.materials.sort();
            _this.activityGroups.sort();
            _this.activities.sort();
            _this.render();
        });
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'click #reload-solution-list': 'populateSolutions',
        'click #add-solution-part': 'addSolutionPart',
        'click #add-question': 'addQuestion',
        'click button[name="implementation-area"]': 'uploadArea',
        'click button[name="show-area"]': 'showArea'
    },

    /*
    * render the view
    */
    render: function(){
        var _this = this,
            html = document.getElementById(this.template).innerHTML,
            template = _.template(html);
        this.el.innerHTML = template({});

        this.solutionPartModal = this.el.querySelector('#solution-part-modal');
        $(this.solutionPartModal).on('hide.bs.modal', function(){
            _this.editView.close();
        })

        this.questionModal = this.el.querySelector('#question-modal');
        $(this.questionModal).on('hide.bs.modal', function(){
            _this.editView.close();
        })

        this.notesArea = this.el.querySelector('textarea[name="notes"]');
        this.notesArea.addEventListener('change', function(){
            _this.activeSolution.save({ documentation: this.value }, {
                patch: true
            })
        })

        this.solutionSelect = this.el.querySelector('select[name="solutions"]');
        $(this.solutionSelect).selectpicker({size: 10});

        this.solutionSelect.addEventListener('change', function(){
            _this.activeSolution = _this.solutions.get(_this.solutionSelect.value);
            if (!_this.activeSolution) return;
            _this.solutionParts = new GDSECollection([], {
                apiTag: 'solutionparts',
                apiIds: [_this.caseStudy.id, _this.keyflowId, _this.activeSolution.id],
                comparator: 'priority'
            });
            _this.questions = new GDSECollection([], {
                apiTag: 'questions',
                apiIds: [_this.caseStudy.id, _this.keyflowId, _this.activeSolution.id]
            });
            var promises = [_this.solutionParts.fetch(), _this.questions.fetch()];
            Promise.all(promises).then(function(){
                _this.solutionParts.sort();
                _this.renderSolution();
            })
        });

        this.populateSolutions();
        this.solutionPartsPanel = this.el.querySelector('#solution-parts-panel');
        this.questionsPanel = this.el.querySelector('#questions-panel');

        this.implAreaText = this.el.querySelector('textarea[name="implementation-area"]');
        var mapDiv = this.el.querySelector('div[name="area-map"]');
        this.areaMap = new Map({
            el: mapDiv
        });
        // map is rendered with wrong size, when tab is not visible -> update size when accessing tab
        $('a[href="#area-tab"]').on('shown.bs.tab', function (e) {
            _this.areaMap.map.updateSize();
        });
        this.areaMap.addLayer('implementation-area', {
            stroke: '#aad400',
            fill: 'rgba(170, 212, 0, 0.1)',
            strokeWidth: 1,
            zIndex: 0
        });
    },

    addSolutionPart: function(){
        var _this = this,
            part = new GDSEModel({}, {
                apiTag: 'solutionparts',
                apiIds: [_this.caseStudy.id, _this.keyflowId, _this.activeSolution.id]
            });
        function onConfirm(part){
            part.save(null, {
                success: function(){
                    _this.solutionParts.add(part);
                    $(_this.solutionPartModal).modal('hide');
                    _this.renderItem(part);
                },
                error: _this.onError
            });
        }
        this.editItem(part, onConfirm);
    },

    clonePart: function(model){
        var _this = this,
            attr = Object.assign({}, model.attributes);
        delete(attr.id)
        delete(attr.url)
        this.solutionParts.create(attr, {
            success: function(clone){
                _this.alert(model.get('name') + ' ' + gettext('successfully cloned'));
                clone.apiTag = 'solutionparts';
                _this.renderItem(clone);
            },
            wait: true,
            error: _this.onError
        })
    },

    addQuestion: function(){
        var _this = this,
            question = new GDSEModel({}, {
                apiTag: 'questions',
                apiIds: [_this.caseStudy.id, _this.keyflowId, _this.activeSolution.id]
            });
        function onConfirm(question){
            question.save(null, {
                success: function(){
                    console.log(question)
                    _this.questions.add(question);
                    $(_this.questionModal).modal('hide');
                    _this.renderItem(question);
                },
                error: _this.onError
            });
        }
        this.editItem(question, onConfirm);
    },

    /* fill selection with solutions */
    populateSolutions: function(){
        var _this = this,
            prevSel = this.solutionSelect.value;
        utils.clearSelect(this.solutionSelect);

        var option = document.createElement('option');
        option.value = -1;
        option.text = gettext('Select');
        option.disabled = true;
        this.solutionSelect.appendChild(option);
        this.categories.forEach(function(category){
            var group = document.createElement('optgroup'),
                solutions = _this.solutions.filterBy({solution_category: category.id});
            group.label = category.get('name');
            solutions.forEach(function(solution){
                var option = document.createElement('option');
                option.value = solution.id;
                option.text = solution.get('name');
                group.appendChild(option);
            })
            _this.solutionSelect.appendChild(group);
        })
        if (prevSel != null) this.solutionSelect.value = prevSel;
        $(this.solutionSelect).selectpicker('refresh');
    },

    renderItem(model){
        var html = document.getElementById('panel-item-template').innerHTML,
            template = _.template(html),
            panelItem = document.createElement('div'),
            itemContent = document.createElement('div'),
            type = model.apiTag,
            _this = this;
        panelItem.classList.add('panel-item');
        if (type === 'solutionparts') panelItem.classList.add('draggable');
        panelItem.style.position = 'absolute';
        panelItem.dataset.id = model.id;
        itemContent.classList.add('noselect', 'item-content');
        var name = (type === 'questions') ? model.get('question') : model.get('name');
        itemContent.innerHTML = template({ name: name });

        var grid = (type === 'solutionparts') ? this.solutionPartsGrid: this.questionsGrid,
            modal = (type === 'solutionparts') ? this.solutionPartModal: this.questionModal;



        var buttonGroup = itemContent.querySelector(".button-box"),
            editBtn = buttonGroup.querySelector("button.edit"),
            removeBtn = buttonGroup.querySelector("button.remove");

        var cloneBtn = document.createElement('button'),
            iconSpan = document.createElement('span');
        cloneBtn.classList.add('square','inverted', 'btn','btn-secondary');
        cloneBtn.title = gettext('clone item');
        iconSpan.classList.add('glyphicon', 'glyphicon-duplicate');
        cloneBtn.appendChild(iconSpan);
        buttonGroup.appendChild(cloneBtn);
        cloneBtn.addEventListener('click', function(){
            _this.clonePart(model);
        })

        editBtn.addEventListener('click', function(){
            function onConfirm(model){
                model.save(null, {
                    success: function(){
                        var name = (type === 'questions') ? model.get('question') : model.get('name');
                        itemContent.querySelector('label[name="name"]').innerHTML = name;
                        $(modal).modal('hide');
                    },
                    error: _this.onError
                });
            }
            _this.editItem(model, onConfirm)
        });
        removeBtn.addEventListener('click', function(){
            _this.removeItem(panelItem, model, grid);
        });
        panelItem.appendChild(itemContent);

        grid.add(panelItem);
    },

    removeItem: function(item, model, grid){
        var _this = this,
            message = gettext("Do you want to delete the selected item?");
        function onConfirm(name){
            model.destroy({
                success: function(){
                    grid.remove(item, { removeElements: true });
                },
                error: _this.onError
            });
        }
        this.confirm({
            message: message,
            onConfirm: onConfirm
        })
    },

    uploadPriorities: function(){
        var _this = this,
            items = this.solutionPartsGrid.getItems(),
            priority = 0;
        items.forEach(function(item){
            var id = item.getElement().dataset.id,
                model = _this.solutionParts.get(id);
            model.save({ priority: priority }, { patch: true });
            priority++;
        })
    },

    editItem: function(model, onConfirm){
        var _this = this,
            type = model.apiTag,
            modal = (type === 'solutionparts') ? this.solutionPartModal: this.questionModal,
            template = (type === 'solutionparts') ? 'solution-part-template': 'question-template',
            View = (type === 'solutionparts') ? SolutionPartView: QuestionView,
            el = modal.querySelector('.modal-body'),
            confirmBtn = modal.querySelector('.confirm');
        $(modal).modal('show');
        this.editView = new View({
            model: model,
            template: template,
            el: el,
            materials: this.materials,
            activityGroups: this.activityGroups,
            activities: this.activities,
            questions: this.questions,
            solutionParts: this.solutionParts
        })
        confirmBtn = utils.removeEventListeners(confirmBtn);
        confirmBtn.addEventListener('click', function(){
            _this.editView.applyInputs();
            onConfirm(model);
        })
    },

    renderItems: function(collection){
        var _this = this;
        collection.forEach(function(model){
            model.apiTag = collection.apiTag,
            _this.renderItem(model);
        })
    },

    renderSolution: function(solution, parts, questions){
        var _this = this,
            solution = this.activeSolution,
            parts = this.solutionParts,
            questions = this.questions;

        if (!solution) return;
        if (this.solutionPartsGrid) this.solutionPartsGrid.destroy();
        if (this.questionsGrid) this.questionsGrid.destroy();

        this.solutionPartsPanel.innerHTML = '';
        this.questionsPanel.innerHTML = '';

        this.solutionPartsGrid = new Muuri(this.solutionPartsPanel, {
            items: '.panel-item',
            dragAxis: 'y',
            layoutDuration: 400,
            layoutEasing: 'ease',
            dragEnabled: true,
            dragSortInterval: 0,
            dragReleaseDuration: 400,
            dragReleaseEasing: 'ease'
        })
        this.questionsGrid = new Muuri(this.questionsPanel, {
            items: '.panel-item',
            dragEnabled: false
        })
        this.solutionPartsGrid.on('dragReleaseEnd', this.uploadPriorities);
        this.el.querySelector('#solution-logic-content').style.visibility = 'visible';
        this.renderItems(parts);
        this.renderItems(questions);
        this.notesArea.value = solution.get('documentation');

        this.areaMap.clearLayer('implementation-area');
        var implArea = solution.get('possible_implementation_area') || '';
        if(implArea) implArea = JSON.stringify(implArea);
        this.implAreaText.value = implArea;
        this.showArea();
    },

    checkGeoJSON: function(geoJSONTxt){
        try {
            var geoJSON = JSON.parse(geoJSONTxt);
        }
        catch(err) {
            this.alert(err);
            return;
        }
        if (!geoJSON.coordinates && !geoJSON.type) {
            this.alert(gettext('GeoJSON needs attributes "type" and "coordinates"'));
        }
        if (!['multipolygon', 'polygon'].includes(geoJSON.type.toLowerCase())){
            this.alert(gettext('type has to be MultiPolygon or Polygon'));
            return;
        }

        return geoJSON;
    },

    showArea: function(){
        var implArea = this.implAreaText.value;
        if (!implArea) return;

        var geoJSON = this.checkGeoJSON(implArea);
        if (!geoJSON) return;

        this.areaMap.clearLayer('implementation-area');
        try {
            var poly = this.areaMap.addPolygon(geoJSON.coordinates, {
                projection: this.projection,
                layername: 'implementation-area',
                tooltip: gettext('Focus area'),
                type: geoJSON.type.toLowerCase()
            });
        }
        catch(err) {
            this.alert(err);
            return;
        }
        this.areaMap.centerOnPolygon(poly, { projection: this.projection });
    },

    uploadArea: function(){
        var geoJSON = this.checkGeoJSON(this.implAreaText.value);
        if (!geoJSON) return;
        var _this = this;

        this.activeSolution.save({ 'possible_implementation_area': geoJSON },{
            success: function(){
                _this.alert(gettext('Upload successful'), gettext('Success'));
            },
            error: _this.onError,
            patch: true
        })
    }
});
return SolutionsLogicView;
}
);
