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
            var caseStudyId = this.caseStudy.id;

            this.mode = options.mode || 0;

            this.categories = [];
            this.stakeholderCategories = new StakeholderCategories([], {
                caseStudyId: caseStudyId
            });

            this.stakeholderCategories.fetch({
                success: function(stakeholderCategories){
                    _this.initStakeholders(stakeholderCategories, caseStudyId);
                    _this.render();
                },
                error: function(){
                    alert("BOOOM!")
                }
            });

        },

        /*
        * dom events (managed by jquery)
        */
        events: {
            'click #add-category-button': 'addCategory'
        },

        initStakeholders: function(stakeholderCategories, caseStudyId){
            var _this = this;
            var deferred = [];
            queryParams = (this.includedOnly) ? {included: 'True'} : {};

            stakeholderCategories.forEach(function(category){
                var stakeholderList = [];
                var stakeholders = new Stakeholders([], {
                    caseStudyId: caseStudyId,
                    stakeholderCategoryId: category.id
                });

                deferred.push(stakeholders.fetch({
                    data: queryParams,
                    success: function (){
                        stakeholders.forEach(function(stakeholder){
                            stakeholderList.push(stakeholder.get('name'));
                        });
                        _this.categories.push({
                            name: category.get('name'),
                            stakeholders: stakeholderList,
                            categoryId: category.id
                        });
                    },
                    error: function(){
                        stakeholderList.push(null);
                    }
                }));
            });

            $.when.apply($, deferred).then(function(){
                _this.render();
            })
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
                    _this.addStakeholder(category);
                });
                div.appendChild(button);
                // add the items
                _this.addPanelItems(panel, category.stakeholders);
            });
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

        addStakeholder: function(category){
            var _this = this;
            function onConfirm(name){
                var stakeholder = new Stakeholder(
                    { name: name },
                    { caseStudyId: _this.caseStudy.id,
                      stakeholderCategoryId: category.categoryId
                    });
                stakeholder.save(null, {
                    success: function(){
                        // remember, _this.categories is an Array of Objects
                        // created in initStakeholders
                        // from https://stackoverflow.com/a/16008853
                        var pos = _this.categories.map(function(e) {
                            return e.categoryId;
                        }).indexOf(category.categoryId);
                        _this.categories[pos].stakeholders.push(name);
                        _this.render();
                    },
                    error: function(){
                        console.log("cannot PUT Stakeholder");
                    }
                });
            }
            this.getName({
                title: gettext('Add Stakeholder'),
                onConfirm: onConfirm
            });
        },

        addCategory: function(){
            var _this = this;
            // save category to the database, and render a local copy of it
            // with the same attributes
            function onConfirm(name){
                var category = new _this.stakeholderCategories.model(
                    { name: name }, { caseStudyId: _this.caseStudy.id });
                var displayCat = {
                    name: name,
                    stakeholders: [],
                    categoryId: category.id
                }
                console.log(category);
                category.save(null, {
                    success: function(){
                        _this.categories.push(displayCat);
                        _this.render();
                    }
                });
            }
            this.getName({
                title: gettext('Add Stakeholder Category'),
                onConfirm: onConfirm
            });
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
