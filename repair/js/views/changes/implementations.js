define(['views/baseview', 'backbone', 'underscore', 'collections/stakeholders',
        'collections/stakeholdercategories', 'visualizations/map', 
        'app-config', 'utils/loader', 'utils/utils', 'bootstrap', 'bootstrap-select'],

function(BaseView, Backbone, _, Stakeholders, StakeholderCategories, 
         Map, config, Loader, utils){
/**
*
* @author Christoph Franke
* @name module:views/ImplementationsView
* @augments BaseView
*/
var ImplementationsView = BaseView.extend(
    /** @lends module:views/ImplementationsView.prototype */
    {

    /**
    * render workshop view on implementations
    *
    * @param {Object} options
    * @param {HTMLElement} options.el                          element the view will be rendered in
    * @param {string} options.template                         id of the script element containing the underscore template to render this view
    * @param {module:models/CaseStudy} options.caseStudy       the casestudy to add implementations to
    *
    * @constructs
    * @see http://backbonejs.org/#View
    */
    initialize: function(options){
        ImplementationsView.__super__.initialize.apply(this, [options]);
        var _this = this;
        this.caseStudy = options.caseStudy;
        this.categories = new StakeholderCategories([], { caseStudyId: this.caseStudy.id });
        this.categories.fetch({
            error: _this.onError,
            success: function(){
                var deferreds = [];
                _this.categories.forEach(function(category){
                
                    var stakeholders = new Stakeholders([], { 
                        caseStudyId: _this.caseStudy.id, 
                        stakeholderCategoryId: category.id 
                    });
                    category.stakeholders = stakeholders;
                    deferreds.push(stakeholders.fetch({ error: _this.onError }))
                });
                
                $.when.apply($, deferreds).then(function(){
                    _this.render();
                });
            }
        })
        this.render();
    },
     
    /*
    * dom events (managed by jquery)
    */
    events: {
        'click #add-implementation': 'addImplementation',
        //'click #implementation-modal .confirm': 'confirmImplementation'
    },

    /*
    * render the view
    */
    render: function(){
        var _this = this;
        var html = document.getElementById(this.template).innerHTML
        var template = _.template(html);
        this.el.innerHTML = template({ categories: this.categories });
        $('#coordinator-select').selectpicker();
    },
    
    renderImplementation: function(){
    
    },
    
    addImplementation: function(){
        var modal = this.el.querySelector('#implementation-modal'),
            okBtn = modal.querySelector('.confirm'),
            _this = this;
            
        function onConfirm(){
            
            okBtn.removeEventListener('click', onConfirm);
            $(modal).modal('hide');
        }
        
        okBtn.addEventListener('click', onConfirm);
        $(modal).modal('show');
    },

});
return ImplementationsView;
}
);
