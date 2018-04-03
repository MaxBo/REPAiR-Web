define(['views/baseview', 'underscore', 'collections/solutioncategories',
        'collections/solutions', 'visualizations/map', 'bootstrap'],

function(BaseView, _, SolutionCategories, Solutions, Map){
    /**
    *
    * @author Christoph Franke
    * @name module:views/SolutionsView
    * @augments BaseView
    */
    var SolutionsView = BaseView.extend(
        /** @lends module:views/SolutionsView.prototype */
        {

        /**
        * render setup view on solutions
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
            SolutionsView.__super__.initialize.apply(this, [options]);
            var _this = this;
            _.bindAll(this, 'renderCategory');

            this.template = options.template;
            this.caseStudy = options.caseStudy;
            this.projection = 'EPSG:4326';
            this.mode = options.mode || 0;
            
            // ToDo: replace with collections fetched from server
            this.categories = new SolutionCategories([], { caseStudyId: this.caseStudy.id })
            
            this.categories.fetch({
                success: _this.render,
                error: _this.onError
            })
        },

        /*
        * dom events (managed by jquery)
        */
        events: {
            'click .chart-control.fullscreen-toggle': 'toggleFullscreen',
            'click #add-solution-category': 'addCategory'
        },

        /*
        * render the view
        */
        render: function(){
            var _this = this;
            var html = document.getElementById(this.template).innerHTML
            var template = _.template(html);
            this.el.innerHTML = template({ keyflows: this.keyflows });
            this.categories.forEach(function(category){
                category.solutions = new Solutions([], { 
                    caseStudyId: _this.caseStudy.id, 
                    solutionCategoryId: category.id
                })
                category.solutions.fetch({
                    success: function(){ _this.renderCategory(category); },
                    error: _this.onError
                })
            });
            $('#solution-modal').on('shown.bs.modal', function () {
                _this.map.map.updateSize();
            });
            
            // lazy way to render workshop mode: just hide all buttons for editing
            // you may make separate views as well
            if (this.mode == 0){
                var btns = this.el.querySelectorAll('button.add, button.edit, button.remove');
                _.each(btns, function(button){
                    button.style.display = 'none';
                });
            }
        },

        renderCategory: function(category){
            var _this = this;
            var panelList = this.el.querySelector('#categories');
            // create the panel (ToDo: use template for panels instead?)
            var div = document.createElement('div'),
                panel = document.createElement('div');
            div.classList.add('col-md-3', 'bordered');
            div.style.margin = '5px';
            var label = document.createElement('label'),
                button = document.createElement('button');
            label.innerHTML = category.get('name');
            
            button.classList.add("btn", "btn-primary", "square", "add");
            var span = document.createElement('span');
            span.classList.add('glyphicon', 'glyphicon-plus');
            button.innerHTML = gettext('Solution');
            button.insertBefore(span, button.firstChild);
            button.addEventListener('click', function(){
            })
            
            panelList.appendChild(div);
            div.appendChild(label);
            div.appendChild(panel);
            div.appendChild(button);
            // add the items
            if (category.solutions)
                category.solutions.forEach(function(solution){
                    _this.addSolutionItem(panel, solution);
                })
        },
        
        addSolutionItem: function(panel, solution){
            var _this = this;
            // render panel item from template (in templates/common.html)
            var html = document.getElementById('panel-item-template').innerHTML,
                template = _.template(html);
            var panelItem = document.createElement('div');
            panelItem.classList.add('panel-item');
            panelItem.innerHTML = template({ name: solution.get('name') });
            panel.appendChild(panelItem);
            // in workshop mode show solution on click on panel, else on click on edit
            var button = (this.mode == 0) ? panelItem: panelItem.querySelector('.edit');
            button.addEventListener('click', function(){
                _this.showSolution(solution);
            })
        },
        
        showSolution: function(solution){
            var category = this.categories.get(solution.get('solution_category'));
            var html = document.getElementById('view-solution-template').innerHTML,
                template = _.template(html);
            var modal = this.el.querySelector('#solution-modal');
            modal.innerHTML = template({ 
                name: solution.get('name'), 
                category: category.get('name'), 
                mode: this.mode 
            });
            this.renderMap('stakeholder-map');
            $(modal).modal('show');
        },
        
        renderMap: function(divid){
            if (this.map){
                this.map.map.setTarget(null);
                this.map.map = null;
                this.map = null;
            }
            this.map = new Map({
                divid: divid, 
            });
            var focusarea = this.caseStudy.get('properties').focusarea;

            this.map.addLayer('background', {
                stroke: '#aad400',
                fill: 'rgba(170, 212, 0, 0.1)',
                strokeWidth: 1,
                zIndex: 0
            },
            );
            // add polygon of focusarea to both maps and center on their centroid
            if (focusarea != null){
                var poly = this.map.addPolygon(focusarea.coordinates[0], { projection: this.projection, layername: 'background', tooltip: gettext('Focus area') });
                this.map.addPolygon(focusarea.coordinates[0], { projection: this.projection, layername: 'background', tooltip: gettext('Focus area') });
                this.centroid = this.map.centerOnPolygon(poly, { projection: this.projection });
                this.map.centerOnPolygon(poly, { projection: this.projection });
            };
        },
        
        addCategory: function(){
            var _this = this;
            function onConfirm(name){
                var category = new _this.categories.model({ name: name }, { caseStudyId: _this.caseStudy.id });
                category.save(null, {
                    success: _this.renderCategory,
                    error: function(model, response) { _this.onError(response) }
                })
            }
            _this.getName({ onConfirm: onConfirm });
        },
    
        toggleFullscreen: function(event){
            event.target.parentElement.classList.toggle('fullscreen');
        }
    });
    return SolutionsView;
}
);