
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
        _.bindAll(this, 'toggleHasQuestion');
        _.bindAll(this, 'toggleAbsolute');
        _.bindAll(this, 'addAffectedFlow');

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
        this.implNewFlowSelect = this.el.querySelector('select[name="impl-new-flow"]');
        this.materialSelect = this.el.querySelector('div[name="material"]');
        this.originSelect = this.el.querySelector('select[name="origin"]');
        this.destinationSelect = this.el.querySelector('select[name="destination"]');
        this.spatialOriginCheck = this.el.querySelector('input[name="origin-in-area"]');
        this.spatialDestinationCheck = this.el.querySelector('input[name="destination-in-area"]');
        this.aInput = this.el.querySelector('input[name="a"]');
        this.bInput = this.el.querySelector('input[name="b"]');
        this.questionSelect = this.el.querySelector('select[name="question"]');
        this.hasQuestionSelect = this.el.querySelector('select[name="has-question"]');
        this.isAbsoluteSelect = this.el.querySelector('select[name="is-absolute"]');

        this.newTargetSelect = this.el.querySelector('select[name="new-target"]');
        this.keepOriginInput = this.el.querySelector('select[name="keep-origin"]');
        this.mapRequestArea = this.el.querySelector('textarea[name="map-request"]');

        $(this.originSelect).selectpicker({size: 10, liveSearch: true, width: 'fit'});
        $(this.destinationSelect).selectpicker({size: 10, liveSearch: true, width: 'fit'});
        $(this.newTargetSelect).selectpicker({size: 10, liveSearch: true});
        this.populateActivitySelect(this.originSelect);
        // ToDo: null allowed for stocks?
        this.populateActivitySelect(this.destinationSelect);
        this.populateActivitySelect(this.newTargetSelect);
        this.populateQuestionSelect();
        this.affectedDiv = this.el.querySelector('#affected-flows');

        this.renderMatFilter(this.materialSelect);

        this.implNewFlowSelect.addEventListener('change', this.toggleNewFlow);
        this.hasQuestionSelect.addEventListener('change', function(){
            _this.toggleHasQuestion();
            _this.toggleAbsolute();
        });
        this.keepOriginInput.addEventListener('change', function(){
            var label = (this.value == "true") ? gettext('destination'): gettext('origin');
            _this.el.querySelector('div[name="origdestlabel"]').innerHTML = label;
        })
        this.isAbsoluteSelect.addEventListener('change', this.toggleAbsolute);
        this.questionSelect.addEventListener('change', this.toggleAbsolute);

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
        // for some reasons jquery doesn't find this element when declared in 'events' attribute
        this.el.querySelector('#affected-flows-tab button.add').addEventListener('click', this.addAffectedFlow);
    },

    toggleNewFlow: function(){
        var implementsNewFlow = this.implNewFlowSelect.value == "true",
            modFlowElements = this.el.querySelectorAll('.modified-flow'),
            newFlowElements = this.el.querySelectorAll('.new-flow');
        modFlowElements.forEach(function(el){
            el.style.display = (implementsNewFlow) ? 'none' :'inline-block';
        })
        newFlowElements.forEach(function(el){
            el.style.display = (implementsNewFlow) ? 'inline-block' :'none';
        })
    },

    toggleHasQuestion: function(){
        var hasQuestion = this.hasQuestionSelect.value == "true"
            questElements = this.el.querySelectorAll('.with-question'),
            noQuestElements = this.el.querySelectorAll('.no-question');

        if (!hasQuestion)
            this.aInput.value = 0;

        noQuestElements.forEach(function(el){
            el.style.display = (hasQuestion) ? 'none' :'inline-block';
        })
        questElements.forEach(function(el){
            el.style.display = (hasQuestion) ? 'inline-block' :'none';
        })
    },

    toggleAbsolute: function(){
        var absElements = this.el.querySelectorAll('.is-absolute'),
            relElements = this.el.querySelectorAll('.is-relative');

        var isAbsolute = false;
        if (this.hasQuestionSelect.value == "false"){
            isAbsolute = this.isAbsoluteSelect.value == "true";
        } else {
            var question = this.questions.get(this.questionSelect.value);
            if (question)
                isAbsolute = question.get('is_absolute') === true;
        }

        relElements.forEach(function(el){
            el.style.display = (isAbsolute) ? 'none' :'inline-block';
        })
        absElements.forEach(function(el){
            el.style.display = (isAbsolute) ? 'inline-block' :'none';
        })
    },

    setInputs: function(){
        var _this = this;
        this.nameInput.value = this.model.get('name') || '';
        this.implNewFlowSelect.value = this.model.get('implements_new_flow');
        this.originSelect.value = this.model.get('implementation_flow_origin_activity') || null;
        this.destinationSelect.value = this.model.get('implementation_flow_destination_activity') || null;
        var spatial = this.model.get('implementation_flow_spatial_application') || 'both';
        spatial = spatial.toLowerCase();
        this.spatialOriginCheck.checked = (spatial == 'origin' || spatial == 'both');
        this.spatialDestinationCheck.checked = (spatial == 'destination' || spatial == 'both');

        this.newTargetSelect.value = this.model.get('new_target_activity') || null;
        this.mapRequestArea.value = this.model.get('map_request') || '';
        var keepOrigin = this.model.get('keep_origin') || false;
        this.keepOriginInput.value = keepOrigin;
        var label = (keepOrigin) ? gettext('destination'): gettext('origin');
        _this.el.querySelector('div[name="origdestlabel"]').innerHTML = label;

        //this.spatialSelect.value = spatial.toLowerCase()
        this.aInput.value = this.model.get('a') || 0;
        this.bInput.value = this.model.get('b') || 0;

        var question = this.model.get('question');
        this.questionSelect.value = question || -1;
        this.hasQuestionSelect.value = (question != null);
        this.isAbsoluteSelect.value = this.model.get('is_absolute');

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
        this.toggleHasQuestion();
        this.toggleAbsolute();

        var affected = this.model.get('affected_flows') || [];
        affected.forEach(function(flow){
            _this.addAffectedFlow(flow);
        })
    },

    applyInputs: function(){
        var _this = this;
        this.model.set('name', this.nameInput.value);
        this.model.set('implements_new_flow', this.implNewFlowSelect.value);
        this.model.set('implementation_flow_origin_activity', (this.originSelect.value != "-1") ? this.originSelect.value: null);
        this.model.set('implementation_flow_destination_activity', (this.destinationSelect.value != "-1") ? this.destinationSelect.value: null);
        var selectedMaterial = this.materialSelect.dataset.selected;
        this.model.set('implementation_flow_material', selectedMaterial);
        var spatial = (this.spatialOriginCheck.checked && this.spatialDestinationCheck.checked) ? 'both':
                      (this.spatialOriginCheck.checked) ? 'origin': 'destination';
        this.model.set('implementation_flow_spatial_application', spatial);
        this.model.set('documentation', '');
        this.model.set('map_request', '');
        this.model.set('a', this.aInput.value);
        this.model.set('b', this.bInput.value);
        var question = this.questionSelect.value;
        var hasQuestion = this.hasQuestionSelect.value == "true";
        this.model.set('question', (hasQuestion && question != "-1") ? question: null);

        this.model.get('is_absolute', this.isAbsoluteSelect.value);

        this.model.set('new_target_activity', (this.newTargetSelect.value != "-1") ? this.newTargetSelect.value: null);
        this.model.set('keep_origin', this.keepOriginInput.value);
        this.model.set('map_request', this.mapRequestArea.value);

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

    renderMatFilter: function(el, width){
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

        var hierarchicalSelect = this.hierarchicalSelect(this.materials, matSelect, {
            onSelect: function(model){
                 el.dataset.selected = model.id;
            },
            width: width,
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
            var li = hierarchicalSelect.querySelector('li[data-value="' + material.id + '"]');
            if (!li) return;
            var a = li.querySelector('a'),
                cls = (flowsInChildren[material.id] > 0) ? 'half': 'empty';
            a.classList.add(cls);
        })
        el.appendChild(hierarchicalSelect);
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
            li = matSelect.querySelector('li[data-value="' + flow['material'] + '"]');
            if(li){
                var matItem = li.querySelector('a');
                matItem.click();
            }
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
