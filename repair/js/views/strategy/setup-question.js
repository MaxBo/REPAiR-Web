
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

        this.template = options.template;
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

        this.nameInput = this.el.querySelector('input[name="name"]');
    },

    setInputs: function(){
        this.nameInput.value = this.model.get('name') || '';
    },

    applyInputs: function(){
        this.model.set('name', this.nameInput.value);
    },

});
return QuestionView;
}
);
