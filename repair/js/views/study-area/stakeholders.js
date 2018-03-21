define(['views/baseview', 'underscore', 'models/stakeholdercategory',
    'collections/stakeholdercategories', 'models/stakeholder',
    'collections/stakeholders'],

function(BaseView, _, StakeholderCategory, StakeholderCategories, Stakeholder,
Stakeholders){
    /**
    *
    * @author Christoph Franke, Balázs Dukai
    * @name module:views/StakeholdersView
    * @augments module:views/BaseView
    */
    var StakeholdersView = BaseView.extend(
        /** @lends module:views/StakeholdersView.prototype */
        {

        /**
        * render setup view on stakeholder categories and stakeholders
        *
        * @param {Object} options
        * @param {HTMLElement} options.el                          element the view will be rendered in
        * @param {string} options.template                         id of the script element containing the underscore template to render this view
        * @param {Number} [options.mode=0]                         workshop (0, default) or setup mode (1)
        * @param {module:models/CaseStudy} options.caseStudy       the casestudy of the stakeholder categories and stakeholders
        *
        * @constructs
        * @see http://backbonejs.org/#View
        */
        initialize: function(options){
            var _this = this;
            _.bindAll(this, 'render');

            this.template = options.template;
            this.caseStudy = options.caseStudy;

            this.mode = options.mode || 0;

            var categories2 = new StakeholderCategories([], {
                caseStudyId: this.caseStudy.id
            });

            categories2.fetch({ success: function(category){
                console.log(category.caseStudyId);
                categories2.forEach(function(category){
                    console.log(category.id);
                    console.log(category.get('name'));
                    // how do i get the caseStudy ID in here?
                    console.log(this.caseStudy.id);
                    var stakeholders = new Stakeholders([], {
                        caseStudyId: this.caseStudyId,
                        stakeholderCategoryId: category.id
                    });
                    stakeholders.fetch({ success: function (){
                        stakeholders.forEach(function(stakeholder){
                            console.log(stakeholder.id);
                            console.log(stakeholder.get('name'));
                        });
                    }});
                }, this.caseStudy);
            }});

            // ToDo: replace with collections fetched from server
            this.categories = [
                { name: 'Government', stakeholders: ['City of Amsterdam'] },
                { name: 'Waste Companies', stakeholders: ['AEB Amsterdam', 'Van Gansewinkel'] },
                { name: 'NGOs', stakeholders: ['Stichting Natuur en Milieu', 'SNV'] }
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
            this.el.innerHTML = template();
            this.renderCategories();

            // lazy way to render workshop mode: just hide all buttons for editing
            // you may make separate views as well
            if (this.mode == 0){
                var btns = this.el.querySelectorAll('button.add, button.edit, button.remove');
                _.each(btns, function(button){
                    button.style.display = 'none';
                });
            }
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
                panelList.appendChild(div);

                var label = document.createElement('label');
                div.appendChild(label);
                div.appendChild(panel);

                var button = document.createElement('button');
                label.innerHTML = category.name;

                button.classList.add("btn", "btn-primary", "square", "add");
                var span = document.createElement('span');
                span.classList.add('glyphicon', 'glyphicon-plus');
                button.innerHTML = gettext('Stakeholder');
                button.title = gettext('add stakeholder');
                button.insertBefore(span, button.firstChild);
                button.addEventListener('click', function(){
                    // ToDo: add functionality for click event (add stakeholder item)
                    // try by adding a browser alert here
                    alert('add stakeholder item');
                })

                div.appendChild(button);
                // add the items
                _this.addPanelItems(panel, category.stakeholders);
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
    return StakeholdersView;
}
);
