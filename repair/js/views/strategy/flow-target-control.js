define(['views/common/baseview', 'collections/gdsecollection',
        'views/status-quo/workshop-flow-assessment', 'underscore',
        'static/css/status-quo.css'],

function(BaseView, GDSECollection, FlowAssessmentWorkshopView, _){
/**
*
* @author Christoph Franke
* @name module:views/FlowTargetControlView
* @augments module:views/BaseView
*/
var FlowTargetControlView = BaseView.extend(
    /** @lends module:views/FlowTargetControlView.prototype */
    {

    /**
    * view to render indicators in strategy
    *
    * @param {Object} options
    */
    initialize: function(options){
        var _this = this;
        FlowTargetControlView.__super__.initialize.apply(this, [options]);
        this.caseStudy = options.caseStudy;
        this.keyflowId = options.keyflowId;
        this.strategy = options.strategy;
        this.render();
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
    },

    render: function(){
        var html = document.getElementById(this.template).innerHTML,
            template = _.template(html),
            _this = this;
        this.el.innerHTML = template();
        this.assessmentView = new FlowAssessmentWorkshopView({
            caseStudy: this.caseStudy,
            el: this.el.querySelector('#modified-indicators'),
            template: 'workshop-flow-assessment-template',
            keyflowId: this.keyflowId,
            strategy: this.strategy
        })
    },

    close: function(){
        this.assessmentView.close();
        FlowTargetControlView.__super__.close.apply(this);
    }
});
return FlowTargetControlView;
}
);


