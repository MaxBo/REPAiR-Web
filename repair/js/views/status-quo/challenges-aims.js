define(['underscore','views/baseview', 'collections/gdsecollection', 
        'models/gdsemodel', 'muuri'],

function(_, BaseView, GDSECollection, GDSEModel, Muuri){
    /**
    *
    * @author Christoph Franke, Balázs Dukai
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

            this.challenges = new GDSECollection([], {
                apiTag: 'challenges',
                apiIds: [this.caseStudy.id],
                comparator: 'priority'
            });
            this.aims = new GDSECollection([], {
                apiTag: 'aims',
                apiIds: [this.caseStudy.id],
                comparator: 'priority'
            });
            
            var promises = [this.challenges.fetch(), this.aims.fetch()]

            Promise.all(promises).then(this.render)
        },

        /*
        * dom events (managed by jquery)
        */
        events: {
            'click #add-challenge-button': 'addChallenge',
            'click #add-aim-button': 'addAim',
            'click #remove-ch-aim-confirmation-modal .confirm': 'confirmRemoval'
        },

        /*
        * render the view
        */
        render: function(){
            var _this = this;
            var html = document.getElementById(this.template).innerHTML
            var template = _.template(html);
            this.el.innerHTML = template();

            var challengesPanel = this.el.querySelector('#challenges').querySelector('.item-panel'),
                aimsPanel = this.el.querySelector('#aims').querySelector('.item-panel'),
                dragEnabled = this.mode == 1;
            this.challengesGrid = new Muuri(challengesPanel, {
                items: '.panel-item',
                dragAxis: 'y',
                layoutDuration: 400,
                layoutEasing: 'ease',
                dragEnabled: dragEnabled,
                dragSortInterval: 0,
                dragReleaseDuration: 400,
                dragReleaseEasing: 'ease'
            })
            this.challengesGrid.on('dragReleaseEnd', function () { 
                _this.uploadPriorities(_this.challengesGrid, _this.challenges) } );
            this.aimsGrid = new Muuri(aimsPanel, {
                items: '.panel-item',
                dragAxis: 'y',
                layoutDuration: 400,
                layoutEasing: 'ease',
                dragEnabled: dragEnabled,
                dragSortInterval: 0,
                dragReleaseDuration: 400,
                dragReleaseEasing: 'ease'
            })
            this.aimsGrid.on('dragReleaseEnd', function () { 
                _this.uploadPriorities(_this.aimsGrid, _this.aims) } );

            this.renderPanel(this.challengesGrid, this.challenges, gettext('Challenge'));
            this.renderPanel(this.aimsGrid, this.aims, gettext('Aim'));

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
        
        uploadPriorities(grid, collection){
            var items = grid.getItems(),
                priority = 0;
            items.forEach(function(item){
                var id = item._element.dataset.id,
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
            var html = document.getElementById('panel-item-template').innerHTML,
                template = _.template(html),
                panelItem = document.createElement('div'),
                itemContent = document.createElement('div'),
                _this = this;
            panelItem.classList.add('panel-item');
            panelItem.style.position = 'absolute';
            panelItem.dataset.id = model.id;
            itemContent.classList.add('noselect', 'item-content');
            itemContent.innerHTML = template({ name: model.get('text') });
            var editBtn = itemContent.querySelector("button.edit");
            var removeBtn = itemContent.querySelector("button.remove");
            editBtn.addEventListener('click', function(){
                _this.editPanelItem(panelItem, model, type);
            });
            removeBtn.addEventListener('click', function(){
                _this.removePanelItem(panelItem, model, grid, type);
            });
            panelItem.appendChild(itemContent);
            grid.add(panelItem);
        },

        addChallenge: function(){
            var _this = this;
            function onConfirm(text){
                var challenge = new GDSEModel({ text: text }, {
                    apiTag: 'challenges',
                    apiIds: [_this.caseStudy.id]
                });
                challenge.save(null, {
                    success: function(){
                        _this.challenges.push({
                            "text": challenge.get('text'),
                            "id": challenge.get('id')
                        });
                        _this.renderItem(_this.challengesGrid, challenge, gettext('Challenge'));
                    },
                    error: _this.onError
                });
            }
            this.getName({
                title: gettext('Add Challenge'),
                onConfirm: onConfirm
            });
        },

        addAim: function(){
            var _this = this;
            function onConfirm(text){
                var aim = new GDSEModel({ text: text }, {
                    apiTag: 'aims',
                    apiIds: [_this.caseStudy.id]
                });
                aim.save(null, {
                    success: function(){
                        _this.aims.push({
                            "text": aim.get('text'),
                            "id": aim.get('id')
                        });
                        _this.renderItem(_this.aimsGrid, aim, gettext('Aim'));
                    },
                    error: function(){
                        console.error("cannot save Aim");
                    }
                });
            }
            this.getName({
                title: gettext('Add Aim'),
                onConfirm: onConfirm
            });
        },

        editPanelItem: function(item, model, type){
            var _this = this;
            var id = item.id;
            var title = gettext("Edit") + " " + type;
            function onConfirm(name){
                model.save({ text: name }, {
                    success: function(){
                        var label = item.querySelector('label');
                        label.innerHTML = name;
                    },
                    error: _this.onError
                });
            }
            this.getName({
                name: model.get('text'),
                title: gettext(title),
                onConfirm: onConfirm
            });
        },

        removePanelItem: function(item, model, grid, type){
            var _this = this;
            var message = gettext("Do you want to delete the selected item?");
            this.confirmationModal.querySelector('.modal-body').innerHTML = message;
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
                message: gettext("Do you want to delete the selected item?"),
                onConfirm: onConfirm
            })
        }
    });
    return ChallengesAimsView;
}
);
