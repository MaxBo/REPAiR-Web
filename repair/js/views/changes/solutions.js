define(['backbone', 'underscore'],

function(Backbone, _,){
    /**
    *
    * @author Christoph Franke
    * @name module:views/SolutionsView
    * @augments Backbone.View
    */
    var SolutionsView = Backbone.View.extend(
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
            var _this = this;
            _.bindAll(this, 'render');

            this.template = options.template;
            this.caseStudy = options.caseStudy;
            
            // ToDo: replace with collections fetched from server
            this.categories = [
                { name: 'Political', solutions: ['Forbid Plastic Bags in Supermarkets'] },
                { name: 'Economic', solutions: ['Raise Fees on Garbage Disposal'] },
                { name: 'Technical', solutions: ['Wood and Insulation Materials', 'Underfloor Collectors'] }
            ]

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
            var _this = this;
            var html = document.getElementById(this.template).innerHTML
            var template = _.template(html);
            this.el.innerHTML = template({ keyflows: this.keyflows });
            this.renderCategories();
        },

        renderCategories(){
            var _this = this;
            var panelList = this.el.querySelector('#categories');
            this.categories.forEach(function(category){
                // create the panel (ToDo: use template for panels instead?)
                var div = document.createElement('div'),
                    panel = document.createElement('div');
                div.classList.add('col-md-3', 'bordered');
                div.style.margin = '5px';
                var label = document.createElement('label'),
                    button = document.createElement('button');
                label.innerHTML = category.name;
                
                button.classList.add("btn", "btn-primary", "square", "add");
                var span = document.createElement('span');
                span.classList.add('glyphicon', 'glyphicon-plus');
                button.innerHTML = gettext('Solution');
                button.insertBefore(span, button.firstChild);
                button.addEventListener('click', function(){
                    // ToDo: add functionality for click event (add stakeholder item)
                })
                
                panelList.appendChild(div);
                div.appendChild(label);
                div.appendChild(panel);
                div.appendChild(button);
                // add the items
                _this.addPanelItems(panel, category.solutions);
            })
        },
        
        addPanelItems(panel, items){
            // render panel items from template (in templates/common.html)
            var html = document.getElementById('panel-item-template').innerHTML,
                template = _.template(html);
            items.forEach(function(item){
                var panelItem = document.createElement('div');
                panelItem.classList.add('panel-item');
                panelItem.innerHTML = template({ name: item });
                panel.appendChild(panelItem);
            })
        },

        /*
        * remove this view from the DOM
        */
        close: function(){
            this.undelegateEvents(); // remove click events
            this.unbind(); // Unbind all local event bindings
            this.el.innerHTML = ''; //empty the DOM element
        },

    });
    return SolutionsView;
}
);