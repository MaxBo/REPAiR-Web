
define(['views/common/baseview', 'underscore', 'collections/gdsecollection',
        'models/gdsemodel', 'app-config', 'viewerjs',
        'utils/utils', 'bootstrap', 'bootstrap-select', 'viewerjs/dist/viewer.css'],

function(BaseView, _, GDSECollection, GDSEModel, config, Viewer, utils){
/**
*
* @author Christoph Franke
* @name module:views/SolutionPartView
* @augments BaseView
*/
var SolutionPartView = BaseView.extend(
    /** @lends module:views/SolutionPartView.prototype */
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
        SolutionPartView.__super__.initialize.apply(this, [options]);
        var _this = this;
        _.bindAll(this, 'toggleHasQuestion');
        _.bindAll(this, 'toggleAbsolute');
        _.bindAll(this, 'addAffectedFlow');

        this.template = 'solution-part-template';

        this.solutions = options.solutions;
        this.solutionParts = options.solutionParts;

        this.materials = options.materials;
        this.activityGroups = options.activityGroups;
        this.activities = options.activities;
        this.questions = options.questions;
        this.areas = options.areas;
        this.processes = options.processes;
        this.scheme = options.scheme || this.model.get('scheme');
        this.render();
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
    },

    /*
    * scheme tags as keys and lists of [title, template, preview-image, example-image] as values
    */
    schemes: {
        'modification': [gettext('Modify Flow'), 'modify-flow-template', 'schemes/modification.png', 'schemes/modification-example.png'],
        'new': [gettext('New Flow'), 'new-flow-template', 'schemes/new.png', 'schemes/new-example.png'],
        'shiftorigin': [gettext('Shift Origin'), 'shift-origin-template', 'schemes/shift-origin.png', 'schemes/shift-origin-example.png'],
        'shiftdestination': [gettext('Shift Destination'), 'shift-destination-template', 'schemes/shift-destination.png', 'schemes/shift-destination-example.png'],
        'prepend': [gettext('Prepend Flow'), 'prepend-flow-template', 'schemes/prepend.png', 'schemes/prepend-example.png'],
        'append': [gettext('Append Flow'), 'append-flow-template', 'schemes/append.png', 'schemes/append-example.png']
    },

    /*
    * render the view
    */
    render: function(){
        var _this = this,
            html = document.getElementById(this.template).innerHTML,
            template = _.template(html);

        var scheme = this.scheme.toLowerCase(),
            schemeAttr = this.schemes[scheme],
            title = schemeAttr[0],
            tmpl = schemeAttr[1],
            schemepreview = schemeAttr[2],
            schemeexample = schemeAttr[3];

        this.el.innerHTML = template({
            schemepreview: schemepreview,
            schemeexample: schemeexample,
            title: title
        });

        html = document.getElementById(tmpl).innerHTML;
        template = _.template(html);
        this.el.querySelector('#definition-content').innerHTML = template({});

        this.viewer = new Viewer.default(this.el.querySelector('#scheme-preview'));

        this.nameInput = this.el.querySelector('input[name="part-name"]');

        this.referenceOriginSelect = this.el.querySelector('select[name="reference-origin"]');
        this.referenceDestinationSelect = this.el.querySelector('select[name="reference-destination"]');
        this.referenceMaterialSelect = this.el.querySelector('div[name="reference-material"]');
        this.referenceProcessSelect = this.el.querySelector('select[name="reference-process"]');
        this.referenceOriginAreaSelect = this.el.querySelector('select[name="reference-origin-area"]');
        this.referenceDestinationAreaSelect = this.el.querySelector('select[name="reference-destination-area"]');

        this.newOriginSelect = this.el.querySelector('select[name="new-origin"]');
        this.newDestinationSelect = this.el.querySelector('select[name="new-destination"]');
        this.newMaterialSelect = this.el.querySelector('div[name="new-material"]');
        this.newProcessSelect = this.el.querySelector('select[name="new-process"]');
        this.newOriginAreaSelect = this.el.querySelector('select[name="new-origin-area"]');
        this.newDestinationAreaSelect = this.el.querySelector('select[name="new-destination-area"]');

        this.aInput = this.el.querySelector('input[name="a"]');
        this.bInput = this.el.querySelector('input[name="b"]');
        this.questionSelect = this.el.querySelector('select[name="question"]');
        this.hasQuestionRadios = this.el.querySelectorAll('input[name="has-question"]');
        this.isAbsoluteRadios = this.el.querySelectorAll('input[name="is-absolute"]');

        $(this.referenceOriginSelect).selectpicker({size: 8, liveSearch: true, width: 'fit'});
        $(this.referenceDestinationSelect).selectpicker({size: 8, liveSearch: true, width: 'fit'});
        $(this.newOriginSelect).selectpicker({size: 8, liveSearch: true, width: 'fit'});
        $(this.newDestinationSelect).selectpicker({size: 8, liveSearch: true, width: 'fit'});

        this.populateActivitySelect(this.referenceOriginSelect);
        this.populateActivitySelect(this.referenceDestinationSelect);
        this.populateActivitySelect(this.newOriginSelect);
        this.populateActivitySelect(this.newDestinationSelect);

        this.populateAreaSelect(this.referenceOriginAreaSelect);
        this.populateAreaSelect(this.referenceDestinationAreaSelect);
        this.populateAreaSelect(this.newOriginAreaSelect);
        this.populateAreaSelect(this.newDestinationAreaSelect);

        this.populateProcessSelect(this.referenceProcessSelect, {defaultOption: gettext('no specific process')});
        this.populateProcessSelect(this.newProcessSelect, {defaultOption: gettext('no change')});

        this.populateQuestionSelect();
        this.affectedDiv = this.el.querySelector('#affected-flows');

        this.renderMatFilter(this.referenceMaterialSelect);
        this.renderMatFilter(this.newMaterialSelect, {defaultOption: gettext('no change')});

        this.setInputs();

        if (this.hasQuestion == null) this.hasQuestion = true;
        this.hasQuestionRadios.forEach(function(radio){
            radio.addEventListener('change', function(){
                _this.hasQuestion = this.value == 'true';
                _this.toggleHasQuestion();
                _this.toggleAbsolute();
            });
        })

        if (this.isAbsolute == null) this.isAbsolute = true;
        this.isAbsoluteRadios.forEach(function(radio){
            radio.addEventListener('change', function(){
                _this.isAbsolute = this.value == 'true';
                _this.toggleAbsolute();
            });
        })
        this.toggleHasQuestion();
        this.toggleAbsolute();

        //this.materialChangeSelect.addEventListener('change', this.toggleNewMaterial);

        // forbid html escape codes in name
        this.nameInput.addEventListener('keyup', function(){
            this.value = this.value.replace(/<|>/g, '')
        })
        // for some reasons jquery doesn't find this element when declared in 'events' attribute
        this.el.querySelector('#affected-flows-tab button.add').addEventListener('click', this.addAffectedFlow);
    },

    toggleHasQuestion: function(){
        var questElements = this.el.querySelectorAll('.with-question'),
            noQuestElements = this.el.querySelectorAll('.no-question'),
            _this = this;

        if (!this.hasQuestion)
            this.aInput.value = 0;

        noQuestElements.forEach(function(el){
            el.style.display = (_this.hasQuestion) ? 'none' :'inline-block';
        })
        questElements.forEach(function(el){
            el.style.display = (_this.hasQuestion) ? 'inline-block' :'none';
        })
    },

    toggleAbsolute: function(){
        var absElements = this.el.querySelectorAll('.is-absolute'),
            relElements = this.el.querySelectorAll('.is-relative'),
            _this = this;

        relElements.forEach(function(el){
            el.style.display = (_this.isAbsolute) ? 'none' :'inline-block';
        })
        absElements.forEach(function(el){
            el.style.display = (_this.isAbsolute) ? 'inline-block' :'none';
        })

        _this.populateQuestionSelect();
    },

    setInputs: function(){

         // hierarchy-select plugin offers no functions to set (actually no functions at all) -> emulate clicking on row
        function setMaterial(matSelect, material){
            var li = matSelect.querySelector('li[data-value="' + material + '"]');
            if(li){
                var matItem = li.querySelector('a');
                matItem.click();
            }
        }

        var _this = this;
        this.nameInput.value = this.model.get('name') || '';
        //this.scheme = this.model.get('scheme');

        var refFlow = this.model.get('flow_reference'),
            changeFlow = this.model.get('flow_changes');

        if (refFlow){
            if (this.referenceOriginSelect) this.referenceOriginSelect.value = refFlow.origin_activity;
            if (this.referenceDestinationSelect) this.referenceDestinationSelect.value = refFlow.destination_activity;
            if (this.referenceMaterialSelect) this.referenceMaterialSelect.select(refFlow.material);
            if (this.referenceProcessSelect) this.referenceProcessSelect.value = refFlow.process || -1;
            if (this.referenceOriginAreaSelect) this.referenceOriginAreaSelect.value = refFlow.origin_area || -1;
            if (this.referenceDestinationAreaSelect) this.referenceDestinationAreaSelect.value = refFlow.destination_area || -1;
        }

        if (changeFlow){
            if (this.newOriginSelect) this.newOriginSelect.value = changeFlow.origin_activity;
            if (this.newDestinationSelect) this.newDestinationSelect.value = changeFlow.destination_activity;
            if (this.newMaterialSelect) this.newMaterialSelect.select(changeFlow.material);
            if (this.newProcessSelect) this.newProcessSelect.value = changeFlow.process || -1;
            if (this.newOriginAreaSelect) this.newOriginAreaSelect.value = changeFlow.origin_area || -1;
            if (this.newDestinationAreaSelect) this.newDestinationAreaSelect.value = changeFlow.destination_area || -1;
        }

        //this.spatialSelect.value = spatial.toLowerCase()
        this.aInput.value = this.model.get('a') || 1;
        this.bInput.value = this.model.get('b') || 0;

        var question = this.model.get('question');
        this.questionSelect.value = question || -1;
        this.hasQuestion = (question != null);
        question = this.questions.get(question);
        this.isAbsolute = (this.hasQuestion) ? question.get('is_absolute'): this.model.get('is_absolute');

        var questValue = (this.hasQuestion) ? 'true': 'false';
        this.hasQuestionRadios.forEach(function(radio){
            radio.checked = radio.value === questValue;
        })
        var absValue = (this.isAbsolute) ? 'true': 'false';
        this.isAbsoluteRadios.forEach(function(radio){
            radio.checked = radio.value === absValue;
        })

        $(this.referenceOriginSelect).selectpicker('refresh');
        $(this.referenceDestinationSelect).selectpicker('refresh');
        $(this.newOriginSelect).selectpicker('refresh');
        $(this.newDestinationSelect).selectpicker('refresh');
        this.toggleHasQuestion();
        this.toggleAbsolute();

        var affected = this.model.get('affected_flows') || [];
        affected.forEach(function(flow){
            _this.addAffectedFlow(flow);
        })
    },

    applyInputs: function(){
        var _this = this;

        var refFlow = {}, changeFlow = {};

        this.model.set('scheme', this.scheme);
        this.model.set('name', this.nameInput.value);

        refFlow.origin_activity = (this.referenceOriginSelect) ? this.referenceOriginSelect.value: null;
        refFlow.destination_activity = (this.referenceDestinationSelect) ? this.referenceDestinationSelect.value : null;
        refFlow.material = (this.referenceMaterialSelect) ? this.referenceMaterialSelect.dataset.selected: null;
        var process = (this.referenceProcessSelect) ? this.referenceProcessSelect.value: null;
        refFlow.process = (process === '-1') ? null: process;
        var area = (this.referenceOriginAreaSelect) ? this.referenceOriginAreaSelect.value: null;
        refFlow.origin_area = (area === '-1') ? null: area;
        area = (this.referenceDestinationAreaSelect) ? this.referenceDestinationAreaSelect.value: null;
        refFlow.destination_area = (area === '-1') ? null: area;
        console.log(refFlow)

        this.model.set('flow_reference', refFlow);
        console.log(refFlow)


        changeFlow.origin_activity = (this.newOriginSelect) ? this.newOriginSelect.value: null;
        changeFlow.destination_activity = (this.newDestinationSelect) ? this.newDestinationSelect.value.value : null;
        changeFlow.material = (this.newMaterialSelect) ? this.newMaterialSelect.dataset.selected: null;
        process = (this.newProcessSelect) ? this.newProcessSelect.value: null;
        changeFlow.process = (process === '-1') ? null: process;
        area = (this.newOriginAreaSelect) ? this.newOriginAreaSelect.value: null;
        changeFlow.origin_area = (area === '-1') ? null: area;
        area = (this.newDestinationAreaSelect) ? this.newDestinationAreaSelect.value: null;
        changeFlow.destination_area = (area === '-1') ? null: area;

        this.model.set('flow_changes', changeFlow);

        this.model.set('documentation', '');
        this.model.set('a', this.aInput.value);
        this.model.set('b', this.bInput.value);
        var question = this.questionSelect.value;
        this.model.set('question', (this.hasQuestion && question != "-1") ? question: null);
        this.model.get('is_absolute', this.isAbsolute);

        var affectedFlowRows = this.affectedDiv.querySelectorAll('.row'),
            affectedFlows = [];

        affectedFlowRows.forEach(function(row){
            var matSelect = row.querySelector('div[name="material"]'),
                originSelect = row.querySelector('select[name="origin"]'),
                destinationSelect = row.querySelector('select[name="destination"]');

            var selectedMaterial = matSelect.dataset.selected;

            var affectedFlow = {
                material: selectedMaterial,
                origin_activity: (originSelect.value != "-1") ? originSelect.value: null,
                destination_activity: (destinationSelect.value != "-1") ? destinationSelect.value: null
            };
            affectedFlows.push(affectedFlow);
        })
        this.model.set('affected_flows', affectedFlows);
    },

    populateQuestionSelect: function(){
        var _this = this;
        utils.clearSelect(this.questionSelect);

        var questions = this.questions.where({is_absolute: this.isAbsolute});

        var option = document.createElement('option');
        option.value = -1;
        option.text = gettext('Select');
        option.disabled = true;
        this.questionSelect.appendChild(option);
        questions.forEach(function(question){
            var option = document.createElement('option');
            option.value = question.id;
            option.text = question.get('question');
            _this.questionSelect.appendChild(option);
        })
    },

    populateActivitySelect: function(select){
        if (select == null) return;
        var _this = this;
        utils.clearSelect(select);

        var option = document.createElement('option');
        option.value = -1;
        option.text = gettext('Select');
        option.disabled = true;
        select.appendChild(option);
        this.activityGroups.forEach(function(activityGroup){
            var group = document.createElement('optgroup'),
                activities = _this.activities.filterBy({activitygroup: activityGroup.id});
            group.label = activityGroup.get('name');
            activities.forEach(function(activity){
                var option = document.createElement('option');
                option.value = activity.id;
                option.text = activity.get('name');
                group.appendChild(option);
            })
            select.appendChild(group);
        })
        $(select).selectpicker('refresh');
    },

    populateAreaSelect: function(select){
        if (select == null) return;
        var _this = this;
        utils.clearSelect(select);

        var option = document.createElement('option');
        option.value = -1;
        option.text = gettext('no spatial restriction');
        select.appendChild(option);
        this.areas.forEach(function(area){
            var option = document.createElement('option');
            option.value = area.id;
            option.text = area.get('question');
            select.appendChild(option);
        })
    },

    populateProcessSelect: function(select, options){
        if (select == null) return;
        var _this = this,
            options = options || {};
        utils.clearSelect(select);

        var option = document.createElement('option');
        option.value = -1;
        option.text = options.defaultOption || gettext('Select');
        select.appendChild(option);
        this.processes.forEach(function(process){
            var option = document.createElement('option');
            option.value = process.id;
            option.text = process.get('name');
            select.appendChild(option);
        })
    },

    renderMatFilter: function(el, options){
        if (el == null) return;
        var _this = this,
            options = options || {};
        this.selectedMaterial = null;
        // select material
        var matSelect = document.createElement('div');
        matSelect.classList.add('materialSelect');
        var select = this.el.querySelector('.hierarchy-select');
        var flowsInChildren = {};
        // count materials in parent, descending level (leafs first)
        this.materials.models.reverse().forEach(function(material){
            var parent = material.get('parent'),
                count = material.get('flow_count') + (flowsInChildren[material.id] || 0);
            flowsInChildren[parent] = (!flowsInChildren[parent]) ? count: flowsInChildren[parent] + count;
        })

        var hierarchicalSelect = this.hierarchicalSelect(this.materials, matSelect, {
            onSelect: function(model){
                 el.dataset.selected = (model) ? model.id: null;
            },
            width: options.width,
            defaultOption: options.defaultOption || gettext('Select'),
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
            var li = hierarchicalSelect.querySelector('li[data-value="' + material.id + '"]');
            if (!li) return;
            var a = li.querySelector('a'),
                cls = (flowsInChildren[material.id] > 0) ? 'half': 'empty';
            a.classList.add(cls);
        })
        el.appendChild(hierarchicalSelect);
        el.select = hierarchicalSelect.select;
    },

    addAffectedFlow: function(flow){
        var row = document.createElement('div');
            html = document.getElementById('affected-flow-row-template').innerHTML,
            template = _.template(html),
            _this = this;
        row.innerHTML = template({});
        row.classList.add('row');
        var matSelect = row.querySelector('div[name="material"]'),
            originSelect = row.querySelector('select[name="origin"]'),
            destinationSelect = row.querySelector('select[name="destination"]'),
            removeBtn = row.querySelector('button.remove');
        this.affectedDiv.appendChild(row);

        this.renderMatFilter(matSelect, '200px');
        $(originSelect).selectpicker({size: 10, liveSearch: true});
        $(destinationSelect).selectpicker({size: 10, liveSearch: true});
        this.populateActivitySelect(originSelect);
        this.populateActivitySelect(destinationSelect);

        if (flow){
            originSelect.value = flow['origin_activity'];
            destinationSelect.value = flow['destination_activity'];
            destinationSelect.value = flow['destination_activity'];
            matSelect.select(flow['material']);
        }

        $(originSelect).selectpicker('refresh');
        $(destinationSelect).selectpicker('refresh');
        removeBtn.addEventListener('click', function(){
            _this.affectedDiv.removeChild(row);
        })
    }

});
return SolutionPartView;
}
);
