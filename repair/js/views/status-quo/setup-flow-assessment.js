define(['views/common/baseview', 'underscore', 'views/status-quo/edit-indicator-flow',
        'collections/gdsecollection'],

function(BaseView, _, IndicatorFlowEditView, GDSECollection){
/**
*
* @author Christoph Franke
* @name module:views/FlowAssessmentSetupView
* @augments module:views/BaseView
*/
var FlowAssessmentSetupView = BaseView.extend(
    /** @lends module:views/FlowsView.prototype */
    {

    /**
    * render setup mode for flow assessment, create indicators
    *
    * @param {Object} options
    * @param {HTMLElement} options.el                     element the view will be rendered in
    * @param {string} options.template                    id of the script element containing the underscore template to render this view
    * @param {module:models/CaseStudy} options.caseStudy  the casestudy to add layers to
    *
    * @constructs
    * @see http://backbonejs.org/#View
    */
    initialize: function(options){
        FlowAssessmentSetupView.__super__.initialize.apply(this, [options]);
        var _this = this;
        _.bindAll(this, 'renderIndicator');

        this.caseStudy = options.caseStudy;
        this.keyflowId = options.keyflowId;
        this.materials = new GDSECollection([], {
            apiTag: 'materials',
            apiIds: [this.caseStudy.id, this.keyflowId ],
            comparator: 'name'
        });
        this.activities = new GDSECollection([], {
            apiTag: 'activities',
            apiIds: [this.caseStudy.id, this.keyflowId ],
            comparator: 'name'
        });
        this.activityGroups = new GDSECollection([], {
            apiTag: 'activitygroups',
            apiIds: [this.caseStudy.id, this.keyflowId ]
        });
        this.indicators = new GDSECollection([], {
            apiTag: 'flowIndicators',
            apiIds: [this.caseStudy.id, this.keyflowId ]
        });

        this.loader.activate();
        var promises = [
            this.activities.fetch(),
            this.indicators.fetch(),
            this.activityGroups.fetch(),
            this.materials.fetch()
        ]
        Promise.all(promises).then(function(){
            _this.activityGroups.sort();
            _this.activities.sort();
            _this.loader.deactivate();
            _this.render();
        })
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'change #indicator-type': 'typeChanged',
        'click #edit-flowindicator-button': 'editIndicator',
        'click #new-flowindicator-button': 'createIndicator',
        'click #upload-flowindicator-button': 'uploadIndicator',
        'click #delete-flowindicator-button': 'deleteIndicator'
    },

    /*
    * render the view
    */
    render: function(){
        var _this = this;
        var html = document.getElementById(this.template).innerHTML
        var template = _.template(html);
        this.el.innerHTML = template({indicators: this.indicators});

        this.indicatorSelect = this.el.querySelector('select[name="indicator"]');
    },

    // fetch and show selected indicator
    editIndicator: function(){
        var selected = this.indicatorSelect.value,
            indicator = this.indicators.get(selected);
        if (indicator){
            // fetch the indicator to reload it
            indicator.fetch({
                success: this.renderIndicator,
                error: this.onError
            })
        }
    },

    // render view on given indicator
    renderIndicator: function(indicator){
        this.el.querySelector('#flowindicator-edit').style.display = 'block';

        this.indicator = indicator;
        this.inputs = {
            name: this.el.querySelector('input[name="name"]'),
            'indicator_type': this.el.querySelector('#indicator-type'),
            unit: this.el.querySelector('input[name="unit"]'),
            description: this.el.querySelector('textarea[name="description"]')
        }
        var type = indicator.get('indicator_type');
        this.el.querySelector('#flowBLi').style.visibility = (type == 'IndicatorAB') ? 'visible': 'hidden';

        this.inputs.name.value = indicator.get('name');
        this.inputs['indicator_type'].value = type;
        this.inputs.unit.value = indicator.get('unit');
        this.inputs.description.value = indicator.get('description');

        // content of Flow A and Flow B tabs
        var tmpltId = 'indicator-flow-edit-template',
            elA = this.el.querySelector('#flow-a-tab'),
            elB = this.el.querySelector('#flow-b-tab');
        var options = {
            caseStudy: this.caseStudy,
            keyflowId: this.keyflowId,
            activityGroups: this.activityGroups,
            activities: this.activities,
            materials: this.materials,
            template: tmpltId
        };
        var optA = Object.assign({
                el: elA,
                indicatorFlow: indicator.get('flow_a')
            }, options),
            optB = Object.assign({
                el: elB,
                indicatorFlow: indicator.get('flow_b')
            }, options);
        this.flowAView = new IndicatorFlowEditView(optA);
        this.flowBView = new IndicatorFlowEditView(optB);
    },

    // event listener for changing flow type
    typeChanged: function(evt){
        var val = evt.target.value,
            aTab = this.el.querySelector('#flowALi'),
            bTab = this.el.querySelector('#flowBLi');
        if (val == 'IndicatorAB'){
            bTab.style.visibility = 'visible';
        }
        else{
            aTab.querySelector('a').click();
            bTab.style.visibility = 'hidden';
        }
    },

    // upload the changes made on inputs of currently opened indicator
    uploadIndicator: function(){
        var _this = this;
        for (var key in this.inputs){
            var value = this.inputs[key].value;
            this.indicator.set(key, value);
        }
        var flowA = this.flowAView.getInputs(),
            flowB = this.flowBView.getInputs();
        this.indicator.set('flow_a', flowA);
        this.indicator.set('flow_b', flowB);
        this.indicator.save(null, {success: function(model){
            var option = _this.indicatorSelect.querySelector('option[value="'+model.id+'"]');
            option.innerHTML = model.get('name');
            _this.alert(gettext('Upload successful'), gettext('Success'));
        }, error: this.onError})
    },

    // create, select and show a new indicator
    createIndicator: function(){
        var _this = this;
        function create(name){
            var indicator = _this.indicators.create(
                { name: name },
                { success: function(){
                    var option = document.createElement('option');
                    option.value = indicator.id;
                    option.innerHTML = name;
                    _this.indicatorSelect.appendChild(option);
                    _this.indicatorSelect.value = indicator.id;
                    _this.renderIndicator(indicator);
                }, error: _this.onError, wait: true }
            );
        }
        this.getName({ onConfirm: create });
    },

    // delete selected indicator
    deleteIndicator: function(){
        var selected = this.indicatorSelect.value,
            indicator = this.indicators.get(selected),
            id = indicator.id
            _this = this;
        if (!indicator) return;
        function destroy(){
            if (indicator == _this.indicator)
                _this.el.querySelector('#flowindicator-edit').style.display = 'none';
            indicator.destroy({
                success: function(){
                    var option = _this.indicatorSelect.querySelector('option[value="' + id + '"]');
                    _this.indicatorSelect.removeChild(option);
                },
                error: _this.onError
            });
        };
        this.confirm({
            message: gettext('Do you want to delete the Indicator') + ' "' + indicator.get('name') + '"?',
            onConfirm: destroy
        })
    },

    close: function(){
        if(this.flowAView) this.flowAView.close();
        if(this.flowBView) this.flowBView.close();
        FlowAssessmentSetupView.__super__.close.call(this);
    }
});
return FlowAssessmentSetupView;
}
);
