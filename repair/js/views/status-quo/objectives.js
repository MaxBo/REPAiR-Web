define(['underscore','views/common/baseview', 'collections/gdsecollection',
        'models/gdsemodel', 'muuri'],

function(_, BaseView, GDSECollection, GDSEModel, Muuri){
    /**
    *
    * @author Christoph Franke
    * @name module:views/ChallengesAimsView
    * @augments Backbone.View
    */
    var ChallengesAimsView = BaseView.extend(
        /** @lends module:views/ChallengesAimsView.prototype */
        {

        /**
        * render setup view on challenges and aims
        *
        * @param {Object} options
        * @param {HTMLElement} options.el                          element the view will be rendered in
        * @param {string} options.template                         id of the script element containing the underscore template to render this view
        * @param {module:models/CaseStudy} options.caseStudy       the casestudy to add challenges and aims to
        *
        * @constructs
        * @see http://backbonejs.org/#View
        */
        initialize: function(options){
            ChallengesAimsView.__super__.initialize.apply(this, [options]);
            var _this = this;

            this.template = options.template;
            this.caseStudy = options.caseStudy;
            this.mode = options.mode || 0;

            this.keyflows = new GDSECollection([], {
                apiTag: 'keyflowsInCaseStudy',
                apiIds: [this.caseStudy.id],
                comparator: 'priority'
            });

            this.challengesGrids = {};
            this.aimsGrids = {};
            this.loader.activate();
            this.keyflows.fetch({
                success: function(){
                    _this.challenges = new GDSECollection([], {
                        apiTag: 'challenges',
                        apiIds: [_this.caseStudy.id],
                        comparator: 'priority'
                    });
                    _this.aims = new GDSECollection([], {
                        apiTag: 'aims',
                        apiIds: [_this.caseStudy.id],
                        comparator: 'priority'
                    });

                    var promises = [_this.challenges.fetch(), _this.aims.fetch()]
                    Promise.all(promises).then(function(){
                        _this.loader.deactivate();
                        _this.render();
                    })
                },
                error: _this.onError
            })
        },

        /*
        * dom events (managed by jquery)
        */
        events: {
            'click .add-challenge-button': 'addChallenge',
            'click .add-aim-button': 'addAim',
            'click #remove-ch-aim-confirmation-modal .confirm': 'confirmRemoval'
        },

        /*
        * render the view
        */
        render: function(){
            var _this = this,
                html = document.getElementById(this.template).innerHTML,
                template = _.template(html);
            this.el.innerHTML = template();
            var keyflowIds = this.keyflows.pluck('id');

            // the general keyflows without a casestudy
            var generalChallenges = this.challenges.filterBy({ keyflow: null }),
                generalAims = this.aims.filterBy({ keyflow: null });
            this.renderKeyflow(gettext('General'), 'general', generalAims, generalChallenges);

            // the other ones in this casestudy
            this.keyflows.forEach(function(keyflow){
                var challenges = _this.challenges.filterBy({ keyflow: keyflow.id }),
                    aims = _this.aims.filterBy({ keyflow: keyflow.id });
                challenges.sort();
                aims.sort();
                // don't render empty keyflow panels in workshop mode
                if (_this.mode == 0 && challenges.length === 0 && aims.length === 0) return;
                _this.renderKeyflow(keyflow.get('name'), keyflow.id, aims, challenges);
            })

            var html_modal = document.getElementById(
                'empty-modal-template').innerHTML;
            this.confirmationModal = document.getElementById(
                'remove-ch-aim-confirmation-modal');
            this.confirmationModal.innerHTML = _.template(html_modal)({
                header: gettext('Remove') });

            // lazy way to render workshop mode: just hide all buttons for editing
            // you may make separate views as well
            if (this.mode == 0){
                var btns = this.el.querySelectorAll('button.add, button.edit, button.remove');
                _.each(btns, function(button){
                    button.style.display = 'none';
                });
            }
        },

        renderKeyflow: function(title, id, aims, challenges){
            var el = document.createElement('div'),
                html = document.getElementById('challenges-aims-detail-template').innerHTML,
                template = _.template(html),
                _this = this;
            this.el.appendChild(el);
            el.innerHTML = template({ id: id, title: title });
            // expand the filter (else rendering of panels messed up)
            el.querySelector('.toggle-details').click();

            var challengesPanel = el.querySelector('.challenges').querySelector('.item-panel'),
                aimsPanel = el.querySelector('.aims').querySelector('.item-panel'),
                dragEnabled = this.mode == 1;
            var challengesGrid = new Muuri(challengesPanel, {
                items: '.panel-item',
                dragAxis: 'y',
                layoutDuration: 400,
                layoutEasing: 'ease',
                dragEnabled: dragEnabled,
                dragSortInterval: 0,
                dragReleaseDuration: 400,
                dragReleaseEasing: 'ease'
            })
            challengesGrid.on('dragReleaseEnd', function () {
                _this.uploadPriorities(challengesGrid, _this.challenges) } );
            this.challengesGrids[id] = challengesGrid;
            var aimsGrid = new Muuri(aimsPanel, {
                items: '.panel-item',
                dragAxis: 'y',
                layoutDuration: 400,
                layoutEasing: 'ease',
                dragEnabled: dragEnabled,
                dragSortInterval: 0,
                dragReleaseDuration: 400,
                dragReleaseEasing: 'ease'
            })
            aimsGrid.on('dragReleaseEnd', function () {
                _this.uploadPriorities(aimsGrid, _this.aims)
            });
            this.aimsGrids[id] = aimsGrid;

            this.renderPanel(challengesGrid, challenges, gettext('Challenge'));
            this.renderPanel(aimsGrid, aims, gettext('Aim'));
        },

        uploadPriorities(grid, collection){
            var items = grid.getItems(),
                priority = 0;
            items.forEach(function(item){
                var id = item.getElement().dataset.id,
                    model = collection.get(id);
                model.set('priority', priority);
                model.save();
                priority++;
            })
        },

        renderPanel(grid, collection, type){
            var _this = this;
            collection.forEach(function(model){
                _this.renderItem(grid, model, type);
            });
        },

        renderItem(grid, model, type){
            var _this = this,
                options = { showButtons: _this.mode != 0 },
                desc = model.get('description');
            if (_this.mode == 0 && desc)
                options['overlayText'] = '<span style="font-size: 29px;" class="glyphicon glyphicon-info-sign"></span>'
            var panelItem = _this.panelItem(model.get('text'), options);
            panelItem.dataset.id = model.id;
            if (this.mode == 1) panelItem.classList.add('draggable');
            var editBtn = panelItem.querySelector("button.edit"),
                removeBtn = panelItem.querySelector("button.remove");
            editBtn.addEventListener('click', function(){
                _this.editPanelItem(panelItem, model, type);
            });
            removeBtn.addEventListener('click', function(){
                _this.removePanelItem(panelItem, model, grid, type);
            });
            grid.add(panelItem);
            // show description on tap in workshop mode
            if (_this.mode == 0 && desc){
                var desc = model.get('description') || '-';
                // html formatting
                desc = desc.replace(/\n/g, "<br/>");
                panelItem.addEventListener('click', function(){
                    _this.info(desc, {
                        title: model.get('text')
                    })
                })
            }
        },

        addChallenge: function(evt){
            var _this = this,
                button = evt.target,
                keyflowId = button.dataset.id,
                grid = this.challengesGrids[keyflowId];

            if (keyflowId === 'general') keyflowId = null;
            function onConfirm(ret){
                var challenge = new GDSEModel(
                    {   keyflow: keyflowId,
                        text: ret.text,
                        description: ret.description
                    },
                    {
                        apiTag: 'challenges',
                        apiIds: [_this.caseStudy.id]
                    }
                );
                challenge.save(null, {
                    success: function(){
                        _this.challenges.push({
                            "text": challenge.get('text'),
                            "description": challenge.get('description'),
                            "id": challenge.get('id')
                        });
                        _this.renderItem(grid, challenge, gettext('Challenge'));
                        _this.uploadPriorities(grid, _this.challenges);
                    },
                    error: _this.onError
                });
            }
            this.getInputs({
                title: gettext('Add Challenge'),
                inputs: {
                    text: {
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

        addAim: function(evt){
            var _this = this,
                button = evt.target,
                keyflowId = button.dataset.id,
                grid = this.aimsGrids[keyflowId];
            if (keyflowId === 'general') keyflowId = null;
            function onConfirm(ret){
                var aim = new GDSEModel(
                    {   keyflow: keyflowId,
                        text: ret.text,
                        description: ret.description
                    },
                    {
                        apiTag: 'aims',
                        apiIds: [_this.caseStudy.id]
                    }
                );
                aim.save(null, {
                    success: function(){
                        _this.aims.push({
                            "text": aim.get('text'),
                            "description": aim.get('description'),
                            "id": aim.get('id')
                        });
                        _this.renderItem(grid, aim, gettext('Aim'));
                        _this.uploadPriorities(grid, _this.aims);
                    },
                    error: _this.onError
                });
            }
            this.getInputs({
                title: gettext('Add Aim'),
                inputs: {
                    text: {
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

        editPanelItem: function(item, model, type){
            var _this = this,
                id = item.id,
                title = gettext("Edit") + " " + type;
            function onConfirm(ret){
                model.save({ text: ret.text, description: ret.description }, {
                    success: function(){
                        var label = item.querySelector('label');
                        label.innerHTML = ret.text;
                    },
                    error: _this.onError
                });
            }
            this.getInputs({
                title: title,
                inputs: {
                    text: {
                        type: 'text',
                        value: model.get('text'),
                        label: gettext('Name')
                    },
                    description: {
                        type: 'textarea',
                        value: model.get('description'),
                        label: gettext('Description')
                    }
                },
                onConfirm: onConfirm
            })
        },

        removePanelItem: function(item, model, grid, type){
            var _this = this,
                message = gettext("Do you want to delete the selected item?");
            this.activeModel = model;
            function onConfirm(name){
                model.destroy({
                    success: function(){
                        grid.remove(item, { removeElements: true });
                    },
                    error: _this.onError
                });
            }
            this.confirm({
                message: message,
                onConfirm: onConfirm
            })
        }
    });
    return ChallengesAimsView;
}
);
