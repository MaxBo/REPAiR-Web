
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

        this.template = options.template;

        this.solutions = options.solutions;

        this.materials = options.materials;
        this.activityGroups = options.activityGroups;
        this.activities = options.activities;
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
        this.fromSelect = this.el.querySelector('select[name="from"]');
        this.toSelect = this.el.querySelector('select[name="to"]');

        $(this.fromSelect).selectpicker({size: 10});
        $(this.toSelect).selectpicker({size: 10});
        this.populateActivityFilter(this.fromSelect);
        this.populateActivityFilter(this.toSelect);

        this.renderMatFilter(this.materialSelect);

        this.implNewFlowInput.addEventListener('change', function(){
            var showTarget = _this.implNewFlowInput.checked,
                flowLi = _this.el.querySelector('a[href="#solution-flow-tab"]'),
                targetLi = _this.el.querySelector('a[href="#target-tab"]');
            flowLi.click();
            targetLi.style.display = (showTarget) ? 'block' :'none';
        })
    },

    populateActivityFilter: function(select){
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
        console.log(this.materials)
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
