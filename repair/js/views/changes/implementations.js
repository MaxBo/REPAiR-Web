define(['views/baseview', 'backbone', 'underscore', 'collections/stakeholders',
        'collections/stakeholdercategories', 'collections/solutioncategories',
        'collections/solutions', 'visualizations/map', 
        'app-config', 'utils/loader', 'utils/utils', 'bootstrap', 'bootstrap-select'],

function(BaseView, Backbone, _, Stakeholders, StakeholderCategories, 
         SolutionCategories, Solutions, Map, config, Loader, utils){
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
        _.bindAll(this, 'renderImplementation');
        
        var _this = this;
        this.caseStudy = options.caseStudy;
        this.stakeholderCategories = new StakeholderCategories([], { caseStudyId: this.caseStudy.id });
        var Implementations = Backbone.Collection.extend({ url: config.api.implementations.format(this.caseStudy.id) });
        this.implementations = new Implementations();
        this.solutionCategories = new SolutionCategories([], { caseStudyId: this.caseStudy.id });
        this.stakeholders = [];
        this.solutions = [];
        $.when(this.implementations.fetch(), this.stakeholderCategories.fetch(), 
               this.solutionCategories.fetch()).then(function(){
            var deferreds = [];
            _this.stakeholderCategories.forEach(function(category){
                var stakeholders = new Stakeholders([], { 
                    caseStudyId: _this.caseStudy.id, 
                    stakeholderCategoryId: category.id 
                });
                category.stakeholders = stakeholders;
                deferreds.push(stakeholders.fetch({ error: _this.onError }))
            });
            _this.solutionCategories.forEach(function(category){
                var solutions = new Solutions([], { 
                    caseStudyId: _this.caseStudy.id, 
                    solutionCategoryId: category.id 
                });
                category.solutions = solutions;
                deferreds.push(solutions.fetch({ error: _this.onError }))
            });
            
            $.when.apply($, deferreds).then(function(){
                _this.render();
            });
               
        })
    },
     
    /*
    * dom events (managed by jquery)
    */
    events: {
        'click #add-implementation': 'addImplementation'
    },

    /*
    * render the view
    */
    render: function(){
        
        var html = document.getElementById(this.template).innerHTML,
            template = _.template(html),
            _this = this;
        this.el.innerHTML = template({ stakeholderCategories: this.stakeholderCategories });
        $('#coordinator-select').selectpicker();
        
        this.implementations.forEach(this.renderImplementation);
        
        document.querySelector('#implementation-modal .confirm').addEventListener('click', function(){ _this.confirmImplementation() })
    },
    
    renderImplementation: function(implementation){
        var html = document.getElementById('implementation-item-template').innerHTML,
            el = document.createElement('div'),
            template = _.template(html),
            stakeholder = null,
            coordId = implementation.get('coordinating_stakeholder'),
            implDiv = this.el.querySelector('#implementations');
            _this = this;
        
        implDiv.appendChild(el);
        for (var i = 0; i < this.stakeholderCategories.length; i++){
            stakeholder = this.stakeholderCategories.at(i).stakeholders.get(coordId);
            if (stakeholder != null) break;
        }
        el.innerHTML = template({ implementation: implementation, stakeholder: stakeholder });
        
        var editBtn = el.querySelector('.edit'),
            removeBtn = el.querySelector('.remove');
        
        editBtn.addEventListener('click', function(){
            _this.editImplementation(implementation, el);
        })
        
        removeBtn.addEventListener('click', function(){
            var message = gettext('Do you really want to delete the implementation and all of its solutions?');
            _this.confirm({ message: message, onConfirm: function(){
                implementation.destroy({
                    success: function() { implDiv.removeChild(el); },
                    error: _this.onError
                })
            }});
        })
    },
    
    editImplementation: function(implementation, item){
        var modal = this.el.querySelector('#implementation-modal'),
            nameInput = modal.querySelector('#implementation-name-input'),
            coordSelect = modal.querySelector('#coordinator-select'),
            _this = this;
        
        nameInput.value = implementation.get('name');
        coordSelect.value = implementation.get('coordinating_stakeholder');
        $(coordSelect).selectpicker('refresh');
        
        this.confirmImplementation = function(){
            implementation.save(
                { 
                    name: nameInput.value, 
                    coordinating_stakeholder: coordSelect.value
                }, 
                {
                    success: function(){
                        item.querySelector('.title').innerHTML = nameInput.value;
                        item.querySelector('.coordinator').innerHTML = coordSelect[coordSelect.selectedIndex].text;
                        $(modal).modal('hide');
                },
                error: function(m, r){ _this.onError(r) }
            })
        };
        
        $(modal).modal('show');
    
    
    },
    
    addImplementation: function(){
        var modal = this.el.querySelector('#implementation-modal'),
            nameInput = modal.querySelector('#implementation-name-input'),
            coordSelect = modal.querySelector('#coordinator-select'),
            _this = this;
        
        nameInput.value = '';
        coordSelect.selectedIndex = 0;
        $(coordSelect).selectpicker('refresh');
        
        this.confirmImplementation = function(){
            var implementation = _this.implementations.create(
                {
                    name: nameInput.value,
                    coordinating_stakeholder: coordSelect.value
                }, 
                { 
                    wait: true,
                    success: function(){
                        _this.renderImplementation(implementation);
                        $(modal).modal('hide');
                    },
                    error: function(model, response) { _this.onError(response) }
                },
            )
        };
        
        $(modal).modal('show');
    }

});
return ImplementationsView;
}
);
