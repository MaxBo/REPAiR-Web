define(['views/common/baseview', 'underscore', 'collections/gdsecollection',
        'models/gdsemodel', 'views/strategy/setup-solution-part',
        'collections/geolocations', 'visualizations/map', 'viewerjs', 'app-config',
        'utils/utils', 'muuri', 'visualizations/map',
        'bootstrap', 'viewerjs/dist/viewer.css', 'bootstrap-select'],

function(BaseView, _, GDSECollection, GDSEModel, SolutionPartView,
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
        _.bindAll(this, 'editSolutionPart');
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
        'click #add-solution-part': 'addSolutionPart'
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
            _this.solutionPartView.close();
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
            var parts = new GDSECollection([], {
                apiTag: 'solutionparts',
                apiIds: [_this.caseStudy.id, _this.keyflowId, _this.activeSolution.id],
                comparator: 'priority'
            });
            parts.fetch({
                success: function(){
                    parts.sort();
                    _this.solutionParts = parts;
                    _this.renderSolution(_this.activeSolution, parts)
                },
                error: _this.onError
            })
        });

        this.populateSolutions();
        this.solutionPartsPanel = this.el.querySelector('#solution-parts-panel');

        var mapDiv = this.el.querySelector('div[name="area-map"]');
        this.areaMap = new Map({
            el: mapDiv
        });
    },

    addSolutionPart: function(){
        var _this = this,
            part = new GDSEModel({}, {
                apiTag: 'solutionparts',
                apiIds: [_this.caseStudy.id, _this.keyflowId, _this.activeSolution.id]
            });
        function onConfirm(part, affectedFlows){
            part.save(null, {
                success: function(){
                    _this.solutionParts.add(part);
                    $(_this.solutionPartModal).modal('hide');
                    _this.renderPartItem(part);
                },
                error: _this.onError
            });
        }
        this.editSolutionPart(part, onConfirm);
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

    renderPartItem(model){
        var html = document.getElementById('panel-item-template').innerHTML,
            template = _.template(html),
            panelItem = document.createElement('div'),
            itemContent = document.createElement('div'),
            _this = this;
        panelItem.classList.add('panel-item');
        panelItem.classList.add('draggable');
        panelItem.style.position = 'absolute';
        panelItem.dataset.id = model.id;
        itemContent.classList.add('noselect', 'item-content');
        itemContent.innerHTML = template({ name: model.get('name') });
        var editBtn = itemContent.querySelector("button.edit"),
            removeBtn = itemContent.querySelector("button.remove");
        editBtn.addEventListener('click', function(){
            function onConfirm(part, affectedFlows){
                part.save(null, {
                    success: function(){
                        itemContent.querySelector('label[name="name"]').innerHTML = part.get('name');
                        $(_this.solutionPartModal).modal('hide');
                    },
                    error: _this.onError
                });
            }
            _this.editSolutionPart(model, onConfirm);
        });
        removeBtn.addEventListener('click', function(){
            _this.removeSolutionPart(panelItem, model);
        });
        panelItem.appendChild(itemContent);
        this.solutionPartsGrid.add(panelItem);
    },

    removeSolutionPart: function(item, model){
        var _this = this,
            message = gettext("Do you want to delete the selected solution part?");
        function onConfirm(name){
            model.destroy({
                success: function(){
                    _this.solutionPartsGrid.remove(item, { removeElements: true });
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

    editSolutionPart: function(solutionPart, onConfirm){
        var _this = this,
            el = this.solutionPartModal.querySelector('.modal-body'),
            confirmBtn = this.solutionPartModal.querySelector('.confirm');
        $(this.solutionPartModal).modal('show');
        this.solutionPartView = new SolutionPartView({
            model: solutionPart,
            template: 'solution-part-template',
            el: el,
            materials: this.materials,
            activityGroups: this.activityGroups,
            activities: this.activities
        })
        confirmBtn = utils.removeEventListeners(confirmBtn);
        confirmBtn.addEventListener('click', function(){
            _this.solutionPartView.applyInputs();
            onConfirm(solutionPart, _this.solutionPartView.affectedFlows);
        })
    },

    renderSolutionParts: function(parts){
        var _this = this;
        parts.forEach(function(part){
            _this.renderPartItem(part);
        })
    },

    renderSolution: function(solution, parts){
        var _this = this;
        if (!solution) return;
        if (this.solutionPartsGrid) this.solutionPartsGrid.destroy();

        this.solutionPartsPanel.innerHTML = '';

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
        this.solutionPartsGrid.on('dragReleaseEnd', this.uploadPriorities);
        this.el.querySelector('#solution-logic-content').style.visibility = 'visible';
        this.renderSolutionParts(parts);
        this.notesArea.value = solution.get('documentation');
        this.areaMap.map.updateSize();
    }
});
return SolutionsLogicView;
}
);
