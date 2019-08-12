
define(['views/common/baseview', 'underscore', 'collections/gdsecollection',
        'models/gdsemodel', 'app-config', 'utils/utils', 'bootstrap',
        'bootstrap-select'],

function(BaseView, _, GDSECollection, GDSEModel, config, utils){
/**
*
* @author Christoph Franke
* @name module:views/QuestionView
* @augments BaseView
*/
var QuestionView = BaseView.extend(
    /** @lends module:views/QuestionView.prototype */
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
        QuestionView.__super__.initialize.apply(this, [options]);
        var _this = this;

        this.template = 'question-template';
        this.solutions = options.solutions;

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

        this.questionInput = this.el.querySelector('input[name="question"]');
        // querySelector gets first element found, first one is the absolute radio button in this case
        this.isAbsoluteInput = this.el.querySelector('input[name="is-absolute"][value="true"]');
        this.isRelativeInput = this.el.querySelector('input[name="is-absolute"][value="false"]');
        this.minInput = this.el.querySelector('input[name="min-value"]');
        this.maxInput = this.el.querySelector('input[name="max-value"]');
        this.stepInput = this.el.querySelector('input[name="step-size"]');

        this.minInput.addEventListener('change', function(){
            _this.maxInput.min = this.value;
            _this.maxInput.value = Math.max(this.value, _this.maxInput.value);
        })

        function setUnit(){
            var unit = (_this.isAbsoluteInput.checked) ? gettext('t/year'): '%',
                unitDivs = _this.el.querySelectorAll('div[name="unit"]');
            unitDivs.forEach(function(div){
                div.innerHTML = unit;
            })
        }

        this.isAbsoluteInput.addEventListener('change', setUnit)
        this.isRelativeInput.addEventListener('change', setUnit)
        this.setInputs();
        setUnit();
        this.maxInput.min =  this.minInput.value;

        // forbid html escape codes in question
        this.questionInput.addEventListener('keyup', function(){
            this.value = this.value.replace(/<|>/g, '')
        })
    },

    setInputs: function(){
        this.questionInput.value = this.model.get('question') || '';
        var is_abs = this.model.get('is_absolute') || false;
        this.isAbsoluteInput.checked = is_abs;
        this.isRelativeInput.checked = !is_abs;
        this.minInput.value = this.model.get('min_value') || 1;
        this.maxInput.value = this.model.get('max_value') || 1000000000000;
        this.stepInput.value = this.model.get('step') || 0.1;
    },

    applyInputs: function(){
        this.model.set('question', this.questionInput.value);
        this.model.set('is_absolute', this.isAbsoluteInput.checked);
        this.model.set('min_value', this.minInput.value);
        this.model.set('max_value', this.maxInput.value);
        this.model.set('step', this.stepInput.value);
    },

});
return QuestionView;
}
);
