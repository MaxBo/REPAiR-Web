define(['views/common/baseview', 'underscore', 'collections/gdsecollection',
        'collections/geolocations', 'visualizations/map', 'viewerjs', 'app-config',
        'utils/utils', 'muuri', 'summernote', 'summernote/dist/summernote.css',
        'bootstrap', 'viewerjs/dist/viewer.css', 'bootstrap-select'],

function(BaseView, _, GDSECollection, GeoLocations, Map, Viewer, config,
         utils, Muuri, summernote){
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
        _.bindAll(this, 'showSolutionPart');

        this.template = options.template;
        this.caseStudy = options.caseStudy;
        this.keyflowId = options.keyflowId;

        this.solutions = options.solutions;

        // ToDo: replace with collections fetched from server
        this.categories = new GDSECollection([], {
            apiTag: 'solutionCategories',
            apiIds: [this.caseStudy.id, this.keyflowId]
        }),

        // ToDo: replace with collections fetched from server
        this.materials = new GDSECollection([], {
            apiTag: 'materials',
            apiIds: [this.caseStudy.id, this.keyflowId]
        }),

        this.activities = new GDSECollection([], {
            apiTag: 'activities',
            apiIds: [this.caseStudy.id, this.keyflowId]
        });
        var promises = [];
        promises.push(this.categories.fetch());
        promises.push(this.materials.fetch());

        this.loader.activate();
        Promise.all(promises).then(function(){
            _this.loader.deactivate();
            _this.render();
        });
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
    },

    /*
    * render the view
    */
    render: function(){
        var _this = this,
            html = document.getElementById(this.template).innerHTML,
            template = _.template(html);
        this.el.innerHTML = template({});

        var notes = this.el.querySelector('div[name="notes"]');

        $(notes).summernote({
            height: 400
        });

        //var testItems = this.el.querySelectorAll('.panel-item');
        //testItems.forEach(function(item){
            //item.addEventListener('click', _this.showSolutionPart)
        //})

        this.solutionSelect = this.el.querySelector('select[name="solutions"]');
        $(this.solutionSelect).selectpicker({size: 10});

        this.solutionSelect.addEventListener('change', function(){
            _this.activeSolution = _this.solutions.get(_this.solutionSelect.value);
            _this.renderSolution(_this.activeSolution);
        });

        this.populateSolutions();
        this.solutionPartsPanel = this.el.querySelector('#solution-parts-panel');

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
        itemContent.innerHTML = template({ name: model.name });
        var editBtn = itemContent.querySelector("button.edit");
        var removeBtn = itemContent.querySelector("button.remove");
        editBtn.addEventListener('click', function(){
            _this.showSolutionPart();
        });
        //removeBtn.addEventListener('click', function(){
            //_this.removePanelItem(panelItem, model, grid, type);
        //});
        panelItem.appendChild(itemContent);
        this.solutionPartsGrid.add(panelItem);
    },

    renderMatFilter: function(el){
        var _this = this;
        this.selectedMaterial = null;
        // select material
        var matSelect = document.createElement('div');
        matSelect.classList.add('materialSelect');
        var select = this.el.querySelector('.hierarchy-select');

        var compAttrBefore = this.materials.comparatorAttr;
        this.materials.comparatorAttr = 'level';
        this.materials.sort();
        var flowsInChildren = {};
        // count materials in parent, descending level (leafs first)
        this.materials.models.reverse().forEach(function(material){
            var parent = material.get('parent'),
                count = material.get('flow_count') + (flowsInChildren[material.id] || 0);
            flowsInChildren[parent] = (!flowsInChildren[parent]) ? count: flowsInChildren[parent] + count;
        })
        this.materials.comparatorAttr = compAttrBefore;
        this.materials.sort();

        this.matSelect = this.hierarchicalSelect(this.materials, matSelect, {
            onSelect: function(model){
                 _this.selectedMaterial = model;
            },
            defaultOption: gettext('All materials'),
            label: function(model, option){
                var compCount = model.get('flow_count'),
                    childCount = flowsInChildren[model.id] || 0,
                    label = model.get('name') + '(' + compCount + ' / ' + childCount + ')';
                return label;
            }
        });

        var matFlowless = this.materials.filterBy({'flow_count': 0});
        // grey out materials not used in any flows in keyflow
        // (do it afterwards, because hierarchical select is build in template)
        matFlowless.forEach(function(material){
            var li = _this.matSelect.querySelector('li[data-value="' + material.id + '"]');
            if (!li) return;
            var a = li.querySelector('a'),
                cls = (flowsInChildren[material.id] > 0) ? 'half': 'empty';
            a.classList.add(cls);
        })
        el.appendChild(matSelect);
    },

    showSolutionPart: function(solutionPart, onConfirm){
        var html = document.getElementById('solution-part-template').innerHTML,
            template = _.template(html),
            modal = this.el.querySelector('#solution-part-modal');
        modal.innerHTML = template();
        $(modal).modal('show');
    },

    renderSolution: function(solution){
        var _this = this;
        if (!solution) return;
        this.el.querySelector('#solution-logic-content').style.display = 'block';

        this.renderPartItem({ name: 'remove flow'});
        this.renderPartItem({ name: 'redirect flow'});
        this.renderPartItem({ name: 'something else'});
    }
});
return SolutionsLogicView;
}
);
