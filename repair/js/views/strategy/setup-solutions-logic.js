define(['views/common/baseview', 'underscore', 'collections/gdsecollection',
        'models/gdsemodel', 'views/strategy/setup-solution-part',
        'views/strategy/setup-question', 'views/strategy/setup-area',
        'collections/geolocations', 'viewerjs', 'app-config',
        'utils/utils', 'muuri', 'bootstrap', 'viewerjs/dist/viewer.css', 'bootstrap-select'],

function(BaseView, _, GDSECollection, GDSEModel, SolutionPartView, QuestionView,
         AreaView, GeoLocations, Viewer, config, utils, Muuri){
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
        this.processes = new GDSECollection([], {
            apiTag: 'processes'
        });

        var promises = [];
        promises.push(this.activities.fetch());
        promises.push(this.activityGroups.fetch());
        promises.push(this.materials.fetch());
        promises.push(this.processes.fetch());

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
        'click #add-solution-part': 'showSchemes',
        'click #schemes-modal button.confirm': 'addSolutionPart',
        'click #add-question': 'addQuestion',
        'click #add-area': 'addArea'
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
        //$(this.solutionPartModal).on('hide.bs.modal', function(){
            //_this.editView.close();
        //})

        this.questionModal = this.el.querySelector('#question-modal');
        $(this.questionModal).on('hide.bs.modal', function(){
            _this.editView.close();
        })

        this.areaModal = this.el.querySelector('#area-modal');
        $(this.areaModal).on('hide.bs.modal', function(){
            _this.editView.close();
        })

        this.schemeSelectModal = this.el.querySelector('#schemes-modal');

        new Viewer.default(this.el.querySelector('#scheme-legend'));

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
            _this.areas = new GDSECollection([], {
                apiTag: 'possibleImplementationAreas',
                apiIds: [_this.caseStudy.id, _this.keyflowId, _this.activeSolution.id]
            });
            var promises = [_this.solutionParts.fetch(),
                            _this.questions.fetch(), _this.areas.fetch()];
            Promise.all(promises).then(function(){
                _this.solutionParts.sort();
                _this.renderSolution();
            })
        });

        this.populateSolutions();
        this.solutionPartsPanel = this.el.querySelector('#solution-parts-panel');
        this.questionsPanel = this.el.querySelector('#questions-panel');
        this.areasPanel = this.el.querySelector('#areas-panel');

        var schemeDivs = this.schemeSelectModal.querySelectorAll('.scheme-preview');
        schemeDivs.forEach(function(div){
            div.addEventListener('click', function(){
                schemeDivs.forEach(function(other){
                    other.classList.remove('selected');
                })
                div.classList.add('selected');
                _this.selectScheme(div);
            })
        })
        this.selectScheme(schemeDivs[0]);
    },

    addSolutionPart: function(){
        var _this = this,
            part = new GDSEModel({}, {
                apiTag: 'solutionparts',
                apiIds: [_this.caseStudy.id, _this.keyflowId, _this.activeSolution.id]
            });
        part.set('scheme', this.selectedScheme)
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

    showSchemes: function(){
        var modal = this.schemeSelectModal;
        $(modal).modal('show');
    },

    selectScheme: function(schemeDiv){
        var title = schemeDiv.querySelector('label').innerHTML,
            desc = schemeDiv.dataset.text,
            src = schemeDiv.querySelector('img').src;
        this.schemeSelectModal.querySelector('#selected-scheme-image').src = src;
        this.schemeSelectModal.querySelector('#selected-scheme-description').innerHTML = desc;
        this.schemeSelectModal.querySelector('#selected-scheme-title').innerHTML = title;
        this.selectedScheme = schemeDiv.dataset.scheme;
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
                    _this.questions.add(question);
                    $(_this.questionModal).modal('hide');
                    _this.renderItem(question);
                },
                error: _this.onError
            });
        }
        this.editItem(question, onConfirm);
    },

    addArea: function(){
        var _this = this,
            area = new GDSEModel({}, {
                apiTag: 'possibleImplementationAreas',
                apiIds: [_this.caseStudy.id, _this.keyflowId, _this.activeSolution.id]
            });
        function onConfirm(question){
            question.save(null, {
                success: function(){
                    _this.areas.add(area);
                    $(_this.areaModal).modal('hide');
                    _this.renderItem(area);
                },
                error: _this.onError
            });
        }
        this.editItem(area, onConfirm);
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
        var name = (type === 'solutionparts') ? model.get('name') : model.get('question');
        if (type === 'questions'){
            var supp = model.get('is_absolute') ? gettext('absolute change') : gettext('relative change');
            name += ' (' + supp + ')';
        }
        itemContent.innerHTML = template({ name: name });

        var grid = (type === 'solutionparts') ? this.solutionPartsGrid:
                   (type === 'possibleImplementationAreas') ? this.areasGrid:
                   this.questionsGrid,
            modal = (type === 'solutionparts') ? this.solutionPartModal:
                    (type === 'possibleImplementationAreas') ? this.areaModal:
                    this.questionModal;

        var buttonGroup = itemContent.querySelector(".button-box"),
            editBtn = buttonGroup.querySelector("button.edit"),
            removeBtn = buttonGroup.querySelector("button.remove");
        if (type === 'solutionparts'){
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
        }
        editBtn.addEventListener('click', function(){
            function onConfirm(model){
                model.save(null, {
                    success: function(){
                        var name = (type === 'solutionparts') ? model.get('name') : model.get('question');
                        if (type === 'questions'){
                            var supp = model.get('is_absolute') ? gettext('absolute change') : gettext('relative change');
                            name += ' (' + supp + ')';
                        }
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
            modal = (type === 'solutionparts') ? this.solutionPartModal:
                    (type === 'possibleImplementationAreas') ? this.areaModal:
                    this.questionModal;
            View = (type === 'solutionparts') ? SolutionPartView:
                   (type === 'possibleImplementationAreas') ? AreaView:
                   QuestionView;
            el = modal.querySelector('.modal-body'),
            confirmBtn = modal.querySelector('.confirm');
        $(modal).modal('show');
        this.editView = new View({
            model: model,
            el: el,
            materials: this.materials,
            activityGroups: this.activityGroups,
            activities: this.activities,
            questions: this.questions,
            solutionParts: this.solutionParts,
            areas: this.areas,
            processes: this.processes,
            caseStudy: this.caseStudy,
            keyflowId: this.keyflowId
        })
        if (type === 'possibleImplementationAreas')
           $(modal).on('shown.bs.modal', function (e) {
                _this.editView.areaMap.map.updateSize();
            });
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

    renderSolution: function(solution){
        var _this = this,
            solution = this.activeSolution;

        if (!solution) return;
        if (this.solutionPartsGrid) this.solutionPartsGrid.destroy();
        if (this.questionsGrid) this.questionsGrid.destroy();
        if (this.areasGrid) this.areasGrid.destroy();

        this.solutionPartsPanel.innerHTML = '';
        this.questionsPanel.innerHTML = '';
        this.areasPanel.innerHTML = '';

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
        this.areasGrid = new Muuri(this.areasPanel, {
            items: '.panel-item',
            dragEnabled: false
        })
        this.solutionPartsGrid.on('dragReleaseEnd', this.uploadPriorities);
        this.el.querySelector('#solution-logic-content').style.visibility = 'visible';
        this.renderItems(this.solutionParts);
        this.renderItems(this.questions);
        this.renderItems(this.areas);
    }
});
return SolutionsLogicView;
}
);
