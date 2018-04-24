define(['views/baseview','underscore', 'models/stakeholdercategory',
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
                    console.error("cannot fetch stakeholderCategories");
                }
            });

        },

        /*
        * dom events (managed by jquery)
        */
        events: {
            'click #add-category-button': 'addCategory',
            'click #remove-stakeholder-confirmation-modal .confirm': 'confirmRemoval'
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
                            stakeholderList.push({
                                "name": stakeholder.get('name'),
                                "id": stakeholder.get('id')
                            });
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

            var html_modal = document.getElementById(
                'empty-modal-template').innerHTML;
            this.confirmationModal = document.getElementById(
                'remove-stakeholder-confirmation-modal');
            this.confirmationModal.innerHTML = _.template(html_modal)({
                header: gettext('Remove') });

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

                var label = document.createElement('label'),
                    button = document.createElement('button'),
                    removeBtn = document.createElement('button');
                label.innerHTML = category.name;
                label.style.marginBottom = '20px';

                button.classList.add("btn", "btn-primary", "square", "add");
                var span = document.createElement('span');
                span.classList.add('glyphicon', 'glyphicon-plus');
                button.innerHTML = gettext('Stakeholder');
                button.title = gettext('add stakeholder');
                button.insertBefore(span, button.firstChild);
                button.addEventListener('click', function(){
                    _this.addStakeholder(category);
                });

                removeBtn.classList.add("btn", "btn-warning", "square", "remove");
                removeBtn.style.float = 'right';
                var span = document.createElement('span');
                removeBtn.title = gettext('Remove category')
                span.classList.add('glyphicon', 'glyphicon-minus');
                removeBtn.appendChild(span);
                removeBtn.addEventListener('click', function(){
                    _this.removeCategory(category);
                })

                div.appendChild(removeBtn);
                div.appendChild(label);
                div.appendChild(panel);
                div.appendChild(button);

                // add the items
                _this.addPanelItems(panel, category);
            });
        },

        addPanelItems(panel, category){
            var _this = this;
            // render panel items from template (in templates/common.html)
            var html = document.getElementById('panel-item-template').innerHTML,
                template = _.template(html);
            category.stakeholders.forEach(function(stakeholder){
                var panelItem = document.createElement('div');
                panelItem.classList.add('panel-item');
                panelItem.innerHTML = template({ name: stakeholder.name });
                var button_edit = panelItem.getElementsByClassName(
                    "btn btn-primary square edit inverted").item(0);
                var button_remove = panelItem.getElementsByClassName(
                    "btn btn-warning square remove").item(0);
                button_edit.addEventListener('click', function(){
                    _this.editStakeholder(stakeholder, category);
                });
                button_remove.addEventListener('click', function(){
                    _this.removeStakeholder(stakeholder, category);
                });
                panel.appendChild(panelItem);
            });
        },

        addStakeholder: function(category){
            var _this = this;
            function onConfirm(name){
                var stakeholder = new Stakeholder(
                    { name: name },
                    { caseStudyId: _this.caseStudy.id,
                      stakeholderCategoryId: category.categoryId }
                );
                stakeholder.save(null, {
                    success: function(){
                        // remember, _this.categories is an Array of Objects
                        // created in initStakeholders
                        // from https://stackoverflow.com/a/16008853
                        var pos = _this.categories.map(function(e) {
                            return e.categoryId;
                        }).indexOf(category.categoryId);
                        _this.categories[pos].stakeholders.push({
                            "name": stakeholder.get('name'),
                            "id": stakeholder.get('id')}
                        );
                        _this.render();
                    },
                    error: function(){
                        console.error("cannot save Stakeholder");
                    }
                });
            }
            this.getName({
                title: gettext('Add Stakeholder'),
                onConfirm: onConfirm
            });
        },

        editStakeholder: function(stakeholder, category){
            var _this = this;
            var id = stakeholder.id;
            function onConfirm(name){
                var model = new Stakeholder(
                    { id: id },
                    { caseStudyId: _this.caseStudy.id,
                      stakeholderCategoryId: category.categoryId }
                );
                model.save({
                    name: name
                }, {
                    success: function(){
                        var catPos = _this.categories.map(function(e) {
                            return e.categoryId;
                        }).indexOf(category.categoryId);
                        var stPos = _this.categories[catPos].stakeholders.map(function(e) {
                            return e.id;
                        }).indexOf(id);
                        _this.categories[catPos].stakeholders[stPos].name = name;
                        _this.render();
                    }
                });
            }
            this.getName({
                name: stakeholder.name,
                title: gettext('Edit Stakeholder'),
                onConfirm: onConfirm
            });
        },

        removeStakeholder: function(stakeholder, category){
            var _this = this;
            var message = gettext("Do you want to delete the selected stakeholder?");
            this.confirmationModal.querySelector('.modal-body').innerHTML = message;
            $(this.confirmationModal).modal('show');
            _this.stakeholder = new Stakeholder(
                {id: stakeholder.id},
                { caseStudyId: _this.caseStudy.id,
                  stakeholderCategoryId: category.categoryId
                });
        },

        confirmRemoval: function() {
            var _this = this;
            $(this.confirmationModal).modal('hide');
            var id = _this.stakeholder.get('id');
            var categoryId = _this.stakeholder.stakeholderCategoryId;
            _this.stakeholder.destroy({
                success: function(){
                    var catPos = _this.categories.map(function(e) {
                        return e.categoryId;
                    }).indexOf(categoryId);
                    var stPos = _this.categories[catPos].stakeholders.map(function(e) {
                        return e.id;
                    }).indexOf(id);
                    _this.categories[catPos].stakeholders.splice(stPos, 1);
                    _this.render();
                }
            });
        },

        addCategory: function(){
            var _this = this;
            // save category to the database, and render a local copy of it
            // with the same attributes
            function onConfirm(name){
                var category = new StakeholderCategory(
                    {name: name},
                    {caseStudyId: _this.caseStudy.id}
                );
                category.save(null,
                {
                    success: function(){
                        var displayCat = {
                            name: name,
                            stakeholders: [],
                            categoryId: category.id
                        };
                        _this.categories.push(displayCat);
                        _this.render();
                    },
                    error: function(){
                        console.error("cannot save StakeholderCategory");
                    }
                });
            }
            this.getName({
                title: gettext('Add Stakeholder Category'),
                onConfirm: onConfirm
            });
        },

        removeCategory: function(cat){
            var _this = this;
            var message = gettext('Do you really want to delete the stakeholder category?');
            _this.confirm({ message: message, onConfirm: function(){
                var category = new StakeholderCategory(
                    {id: cat.categoryId},
                    {caseStudyId: _this.caseStudy.id}
                );
                category.destroy({
                    success: function(){
                        var pos = _this.categories.map(function(e) {
                            return e.categoryId;
                        }).indexOf(cat.categoryId);
                        _this.categories.splice(pos, 1);
                        _this.render();
                    }
                });
            }});
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
