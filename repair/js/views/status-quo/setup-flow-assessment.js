define(['views/baseview', 'underscore'],

function(BaseView, _){
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
        
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
    },

    /*
    * render the view
    */
    //render: function(){
        ////var _this = this;
        ////var html = document.getElementById(this.template).innerHTML
        ////var template = _.template(html);
        ////this.el.innerHTML = template();
        ////this.typeSelect = this.el.querySelector('#data-view-type-select');
        ////this.renderMatFilter();
        ////this.renderNodeFilters();
        ////this.renderSankey();
    //},


});
return FlowAssessmentSetupView;
}
);