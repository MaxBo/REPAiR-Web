define(['views/baseview', 'underscore'],

function(BaseView, _){
/**
*
* @author Christoph Franke
* @name module:views/IndicatorFlowsEditView
* @augments module:views/BaseView
*/
var IndicatorFlowsEditView = BaseView.extend(
    /** @lends module:views/FlowsView.prototype */
    {

    /**
    * render view on flow (A/B) settings for indicators
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
        IndicatorFlowsEditView.__super__.initialize.apply(this, [options]);
        this.render();
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
    },
    
    render: function(){
        var _this = this;
        var html = document.getElementById(this.template).innerHTML
        var template = _.template(html);
        this.el.innerHTML = template();
        
        var levelSelect = this.el.querySelector('select[name="level-select"]'),
            groupSelect = this.el.querySelector('select[name="group"]'),
            activitySelect = this.el.querySelector('select[name="activity"]'),
            actorSelect = this.el.querySelector('select[name="actor"]');

        levelSelect.addEventListener('change', function(evt){
            var level = this.value,
                multi, 
                hide = [];
                
            [actorSelect, groupSelect, activitySelect].forEach(function(sel){
                sel.parentElement.style.display = 'block';
                sel.selectedIndex = 0;
                sel.removeAttribute('multiple');
            })
            if (level == 'actor'){
                multi = actorSelect;
            }
            else if (level == 'activity'){
                multi = activitySelect;
                hide = [actorSelect];
            }
            else {
                multi = groupSelect;
                hide = [actorSelect, activitySelect];
            }
            multi.setAttribute('multiple', true);
            hide.forEach(function(s){
                s.parentElement.style.display = 'none';
            })
        })
        levelSelect.value = 'actor';
        levelSelect.dispatchEvent(new Event('change'))
    
    }

});
return IndicatorFlowsEditView;
}
);