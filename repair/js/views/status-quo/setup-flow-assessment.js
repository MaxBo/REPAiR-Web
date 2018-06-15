define(['views/baseview', 'underscore', 'views/status-quo/edit-indicator-flows',
        'collections/gdsecollection'],

function(BaseView, _, IndicatorFlowsEditView, GDSECollection){
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
        
        this.caseStudy = options.caseStudy;
        this.keyflowId = options.keyflowId;
        this.materials = new GDSECollection([], { 
            apiTag: 'materials',
            apiIds: [this.caseStudy.id, this.keyflowId ]
        });
        this.activities = new GDSECollection([], { 
            apiTag: 'activities',
            apiIds: [this.caseStudy.id, this.keyflowId ]
        });
        this.activityGroups = new GDSECollection([], { 
            apiTag: 'activitygroups',
            apiIds: [this.caseStudy.id, this.keyflowId ]
        });
        
        this.loader.activate();
        var promises = [
            this.activities.fetch(),
            this.activityGroups.fetch(),
            this.materials.fetch()
        ]
        Promise.all(promises).then(function(){
            _this.loader.deactivate();
            _this.render();
        })
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'change #indicator-type': 'typeChanged'
    },

    /*
    * render the view
    */
    render: function(){
        var _this = this;
        var html = document.getElementById(this.template).innerHTML
        var template = _.template(html);
        this.el.innerHTML = template();
        
        this.el.querySelector('#flowBLi').style.visibility = 'hidden';
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
        var optA = Object.assign({el: elA}, options),
            optB = Object.assign({el: elB}, options);
        this.flowAView = new IndicatorFlowsEditView(optA);
        this.flowBView = new IndicatorFlowsEditView(optB);
    },

    typeChanged: function(evt){
        var val = evt.target.value,
            aTab = this.el.querySelector('#flowALi'),
            bTab = this.el.querySelector('#flowBLi');
        if (val == 'a/b'){
            bTab.style.visibility = 'visible';
        }
        else{
            aTab.querySelector('a').click();
            bTab.style.visibility = 'hidden';
        }
    },
    
    close: function(){
        FlowAssessmentSetupView.__super__.close();
        this.flowAView.close();
        this.flowBView.close();
    }
});
return FlowAssessmentSetupView;
}
);