define(['views/common/baseview', 'underscore', 'collections/gdsecollection'],

function(BaseView, _, GDSECollection){
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
        StakeholdersView.__super__.initialize.apply(this, [options]);
        var _this = this;

        this.template = options.template;
        this.caseStudy = options.caseStudy;
        var caseStudyId = this.caseStudy.id;

        this.mode = options.mode || 0;

        this.stakeholderCategories = new GDSECollection([], {
            apiTag: 'stakeholderCategories',
            apiIds: [ caseStudyId ]
        });

        this.stakeholderCategories.fetch({
            success: function(stakeholderCategories){
                _this.initStakeholders(stakeholderCategories, caseStudyId);
            },
            error: _this.onError
        });

    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'click #add-category-button': 'addCategory',
    },

    initStakeholders: function(stakeholderCategories, caseStudyId){
        var _this = this;
        var promises = [];

        stakeholderCategories.forEach(function(category){
            var stakeholders = new GDSECollection([], {
                apiTag: 'stakeholders',
                apiIds: [ caseStudyId, category.id ]
            });

            promises.push(stakeholders.fetch({
                success: function (){
                    category.stakeholders = stakeholders;
                },
                error: _this.onError
            }));
        });

        Promise.all(promises).then(function(){
            _this.render();
        })
    },

    /*
    * render the view
    */
    render: function(){
        if (this.mode === 0 && this.stakeholderCategories.size() == 0){
            var warning = document.createElement('h3');
            warning.style.margin = '30px';
            warning.innerHTML = gettext('The stakeholders are not set up.');
            this.el.innerHTML = warning.outerHTML;
            return;
        }
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
        this.stakeholderCategories.forEach(function(category){
            // create the panel (ToDo: use template for panels instead?)
            var div = document.createElement('div'),
                panel = document.createElement('div');
            div.classList.add('col-md-3', 'bordered');
            div.style.margin = '5px';
            panelList.appendChild(div);

            var label = document.createElement('label'),
                button = document.createElement('button'),
                editBtn = document.createElement('button'),
                removeBtn = document.createElement('button');
            label.innerHTML = category.get('name');
            label.style.marginBottom = '20px';

            if (_this.mode != 0){
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

                editBtn.classList.add("btn", "btn-primary", "square", "inverted");
                editBtn.style.float = 'right';
                editBtn.style.marginRight = '3px';
                var span = document.createElement('span');
                editBtn.title = gettext('Edit category')
                span.classList.add('glyphicon', 'glyphicon-pencil');
                editBtn.appendChild(span);
                editBtn.addEventListener('click', function(){
                    _this.editCategory(category);
                })
                div.appendChild(removeBtn);
                div.appendChild(editBtn);
            }

            div.appendChild(label);
            div.appendChild(panel);
            if (_this.mode != 0) div.appendChild(button);

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
            panelItem.classList.add('noselect');
            panelItem.innerHTML = template({ name: stakeholder.get('name') });
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

            // show description on tap in workshop mode
            if (_this.mode == 0){
                var desc = stakeholder.get('description') || '-';
                // html formatting
                desc = desc.replace(/\n/g, "<br/>");
                panelItem.addEventListener('click', function(){
                    _this.info(desc, {
                        title: stakeholder.get('name')
                    })
                })
            }
        });
    },

    addStakeholder: function(category){
        var _this = this;
        function onConfirm(ret){
            var stakeholder = category.stakeholders.create(
                {
                    name: ret.name,
                    description: ret.description
                },
                {
                    success: _this.render,
                    error: _this.onError,
                    wait: true
                }
            );
        }
        this.getInputs({
            title: gettext('Add Stakeholder'),
            inputs: {
                name: {
                    type: 'text',
                    label: gettext('Name')
                },
                description: {
                    type: 'textarea',
                    label: gettext('Description')
                }
            },
            onConfirm: onConfirm
        })
    },

    editStakeholder: function(stakeholder, category){
        var _this = this;
        var id = stakeholder.id;
        function onConfirm(ret){
            stakeholder.save(
                {
                    name: ret.name,
                    description: ret.description
                },
                {
                    success: _this.render,
                    error: _this.onError,
                    wait: true
                }
            );
        }
        this.getInputs({
            title: gettext('Edit Stakeholder'),
            inputs: {
                name: {
                    type: 'text',
                    value: stakeholder.get('name'),
                    label: gettext('Name')
                },
                description: {
                    type: 'textarea',
                    value: stakeholder.get('description'),
                    label: gettext('Description')
                }
            },
            onConfirm: onConfirm
        })
    },

    editModal: function(name, description, onConfirm){
        this.getInputs(values)
    },

    removeStakeholder: function(stakeholder, category){
        var _this = this;
        function onConfirm(){
            stakeholder.destroy({
                success: _this.render,
                error: _this.onError,
                wait: true
            })
        }
        var message = gettext('Do you want to delete the selected stakeholder?');
        this.confirm({ message: message, onConfirm: onConfirm })
    },

    addCategory: function(){
        var _this = this;
        // save category to the database, and render a local copy of it
        // with the same attributes
        function onConfirm(name){
            _this.stakeholderCategories.create({name: name}, {
                success: _this.render,
                error: _this.onError,
                wait: true
            });
        }
        this.getName({
            title: gettext('Add Stakeholder Category'),
            onConfirm: onConfirm
        });
    },

    removeCategory: function(category){
        var _this = this;
        var message = gettext('Do you really want to delete the stakeholder category?');
        function onConfirm(){
            category.destroy({
                success: _this.render,
                error: _this.onError,
                wait: true
            })
        }
        this.confirm({ message: message, onConfirm: onConfirm })
    },

    editCategory: function(category){
        var _this = this;
        function onConfirm(name){
            category.save(
                {
                    name: name,
                },
                {
                    success: _this.render,
                    error: _this.onError,
                    wait: true
                }
            );
        }
        this.getName({
            title: gettext('Edit Category'),
            name: category.get('name'),
            onConfirm: onConfirm
        })
    },

});
return StakeholdersView;
}
);
