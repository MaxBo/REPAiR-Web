
define(['views/common/baseview', 'underscore', 'collections/gdsecollection',
        'models/gdsemodel', 'app-config', 'utils/utils', 'bootstrap',
        'bootstrap-select'],

function(BaseView, _, GDSECollection, GDSEModel, config, utils){
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
        _.bindAll(this, 'toggleNewFlow');

        this.template = options.template;

        this.solutions = options.solutions;

        this.materials = options.materials;
        this.activityGroups = options.activityGroups;
        this.activities = options.activities;
        this.questions = options.questions;
        this.render();
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

        this.nameInput = this.el.querySelector('input[name="name"]');
        this.implNewFlowInput = this.el.querySelector('input[name="impl-new-flow"]');
        this.materialSelect = this.el.querySelector('div[name="material"]');
        this.originSelect = this.el.querySelector('select[name="origin"]');
        this.destinationSelect = this.el.querySelector('select[name="destination"]');
        this.spatialOriginCheck = this.el.querySelector('input[name="origin-in-area"]');
        this.spatialDestinationCheck = this.el.querySelector('input[name="destination-in-area"]');
        this.aInput = this.el.querySelector('input[name="a"]');
        this.bInput = this.el.querySelector('input[name="b"]');
        this.questionSelect = this.el.querySelector('select[name="question"]');

        this.newTargetSelect = this.el.querySelector('select[name="new-target"]');
        this.keepOriginInput = this.el.querySelector('select[name="keep-origin"]');
        this.mapRequestArea = this.el.querySelector('textarea[name="map-request"]');

        $(this.originSelect).selectpicker({size: 10});
        $(this.destinationSelect).selectpicker({size: 10});
        $(this.newTargetSelect).selectpicker({size: 10});
        this.populateActivitySelect(this.originSelect);
        // ToDo: null allowed for stocks?
        this.populateActivitySelect(this.destinationSelect);
        this.populateActivitySelect(this.newTargetSelect);
        this.populateQuestionSelect();

        this.renderMatFilter(this.materialSelect);

        this.implNewFlowInput.addEventListener('change', this.toggleNewFlow)
        this.setInputs(this.model);

        // at least one checkbox has to be checked
        this.spatialOriginCheck.addEventListener('change', function(){
            if (!this.checked) _this.spatialDestinationCheck.checked = true;
        })
        this.spatialDestinationCheck.addEventListener('change', function(){
            if (!this.checked) _this.spatialOriginCheck.checked = true;
        })

        // forbid html escape codes in name
        this.nameInput.addEventListener('keyup', function(){
            this.value = this.value.replace(/<|>/g, '')
        })
    },

    toggleNewFlow: function(){
        var showTarget = this.implNewFlowInput.checked,
            flowLi = this.el.querySelector('a[href="#solution-flow-tab"]'),
            targetLi = this.el.querySelector('a[href="#target-tab"]');
        flowLi.click();
        targetLi.style.display = (showTarget) ? 'block' :'none';
    },

    setInputs: function(){
        this.nameInput.value = this.model.get('name') || '';
        this.implNewFlowInput.checked = this.model.get('implements_new_flow');
        this.originSelect.value = this.model.get('implementation_flow_origin_activity') || null;
        this.destinationSelect.value = this.model.get('implementation_flow_destination_activity') || null;
        var spatial = this.model.get('implementation_flow_spatial_application') || 'both';
        spatial = spatial.toLowerCase();
        this.spatialOriginCheck.checked = (spatial == 'origin' || spatial == 'both');
        this.spatialDestinationCheck.checked = (spatial == 'destination' || spatial == 'both');

        this.newTargetSelect.value = this.model.get('new_target_activity') || null;
        this.mapRequestArea.value = this.model.get('map_request') || '';
        this.keepOriginInput.value = this.model.get('keep_origin') || false;

        //this.spatialSelect.value = spatial.toLowerCase()
        this.aInput.value = this.model.get('a') || 0;
        this.bInput.value = this.model.get('b') || 0;
        this.questionSelect.value = this.model.get('question') || -1;

        // hierarchy-select plugin offers no functions to set (actually no functions at all) -> emulate clicking on row
        var material = this.model.get('implementation_flow_material'),
            li = this.materialSelect.querySelector('li[data-value="' + material + '"]');
        if(li){
            var matItem = li.querySelector('a');
            matItem.click();
        }
        $(this.originSelect).selectpicker('refresh');
        $(this.destinationSelect).selectpicker('refresh');
        $(this.newTargetSelect).selectpicker('refresh');
        this.toggleNewFlow();
    },

    applyInputs: function(){
        this.model.set('name', this.nameInput.value);
        this.model.set('implements_new_flow', this.implNewFlowInput.checked);
        this.model.set('implementation_flow_origin_activity', (this.originSelect.value != "-1") ? this.originSelect.value: null);
        this.model.set('implementation_flow_destination_activity', (this.destinationSelect.value != "-1") ? this.destinationSelect.value: null);
        this.model.set('implementation_flow_material', (this.selectedMaterial) ? this.selectedMaterial.id: null);
        var spatial = (this.spatialOriginCheck.checked && this.spatialDestinationCheck.checked) ? 'both':
                      (this.spatialOriginCheck.checked) ? 'origin': 'destination';
        this.model.set('implementation_flow_spatial_application', spatial);
        this.model.set('documentation', '');
        this.model.set('map_request', '');
        this.model.set('a', this.aInput.value);
        this.model.set('b', this.bInput.value);
        var question = this.questionSelect.value;
        this.model.set('question', (question == "-1") ? null: question);

        this.model.set('new_target_activity', (this.newTargetSelect.value != "-1") ? this.newTargetSelect.value: null);
        this.model.set('keep_origin', this.keepOriginInput.value);
        this.model.set('map_request', this.mapRequestArea.value);
    },

    populateQuestionSelect: function(){
        var _this = this;
        utils.clearSelect(this.questionSelect);

        var option = document.createElement('option');
        option.value = -1;
        option.text = gettext('Select');
        option.disabled = true;
        this.questionSelect.appendChild(option);
        this.questions.forEach(function(question){
            var option = document.createElement('option');
            option.value = question.id;
            option.text = question.get('question');
            _this.questionSelect.appendChild(option);
        })
    },

    populateActivitySelect: function(select){
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

    renderMatFilter: function(el){
        var _this = this;
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

        this.matSelect = this.hierarchicalSelect(this.materials, matSelect, {
            onSelect: function(model){
                 _this.selectedMaterial = model;
            },
            defaultOption: gettext('Select'),
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
    }

});
return SolutionPartView;
}
);
