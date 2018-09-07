define(['views/common/baseview', 'views/common/flows', 'underscore'],

function(BaseView, FlowsView, _){
/**
*
* @author Christoph Franke
* @name module:views/FlowsSetupView
* @augments module:views/BaseView
*/
var FlowsSetupView = BaseView.extend(
    /** @lends module:views/FlowsSetupView.prototype */
    {

    /**
    * render view to show keyflows in casestudy
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
        FlowsSetupView.__super__.initialize.apply(this, [options]);
        this.caseStudy = options.caseStudy;
        this.keyflowId = options.keyflowId;
        this.render();
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'click #edit-flowfilter-button': 'editFilter',
        'click #new-flowfilter-button': 'createFilter',
        //'click #upload-flowindicator-button': 'uploadIndicator',
        'click #delete-flowfilter-button': 'deleteFilter'
    },

    /*
    * render the view
    */
    render: function(){
        var _this = this,
            html = document.getElementById(this.template).innerHTML,
            template = _.template(html);
        this.el.innerHTML = template();
        this.renderFlowsView();
    },

    renderFlowsView: function(){
        var el = this.el.querySelector('#setup-flows-content'),
            _this = this;
        el.style.visibility = 'hidden';
        this.loader.activate();
        this.flowsView = new FlowsView({
            caseStudy: this.caseStudy,
            el: el,
            template: 'flows-template',
            keyflowId: this.keyflowId,
            callback: function(){
                _this.loader.deactivate();
                // expand filter section
                _this.el.querySelector('#toggle-filter-section').click();
            }
        })
    },

    createFilter: function(){
        this.flowsView.el.style.visibility = 'visible';
    }


});
return FlowsSetupView;
}
);

