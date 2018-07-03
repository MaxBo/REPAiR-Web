define(['underscore','views/baseview', 'collections/gdsecollection', 
        'models/gdsemodel'],

function(_, BaseView, GDSECollection, GDSEModel){
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

            _this.challenges = [];
            this.challengesModel = new GDSECollection([], {
                apiTag: 'challenges',
                apiIds: [this.caseStudy.id]
            });
            _this.aims = [];
            this.aimsModel = new GDSECollection([], {
                apiTag: 'aims',
                apiIds: [this.caseStudy.id]
            });
            
            var promises = [
                this.challengesModel.fetch({
                    success: function(challenges){
                        _this.initItems(challenges, _this.challenges,
                             "Challenge");
                    },
                    error: this.onError
                }),
                this.aimsModel.fetch({
                    success: function(aims){
                        _this.initItems(aims, _this.aims, "Aim");
                    },
                    error: this.onError
                })
            ]

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

        initItems: function(items, list, type){
            items.forEach(function(item){
                list.push({
                    "text": item.get('text'),
                    "id": item.get('id'),
                    "type": type
                });
            });
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
                aimsPanel = this.el.querySelector('#aims').querySelector('.item-panel');
            this.renderPanel(challengesPanel, this.challenges);
            this.renderPanel(aimsPanel, this.aims);

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

        renderPanel(panel, items){
            var _this = this;
            var html = document.getElementById('panel-item-template').innerHTML,
                template = _.template(html);
            items.forEach(function(item){
                var panelItem = document.createElement('div');
                panelItem.classList.add('panel-item');
                panelItem.classList.add('noselect');
                panelItem.innerHTML = template({ name: item.text });
                var button_edit = panelItem.getElementsByClassName(
                    "btn btn-primary square edit inverted").item(0);
                var button_remove = panelItem.getElementsByClassName(
                    "btn btn-warning square remove").item(0);
                button_edit.addEventListener('click', function(){
                    _this.editPanelItem(item, items);
                });
                button_remove.addEventListener('click', function(){
                    _this.removePanelItem(item, items);
                });
                panel.appendChild(panelItem);
            });
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
                            "id": challenge.get('id'),
                            "type": "Challenge"
                        });
                        _this.render();
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
                            "id": aim.get('id'),
                            "type": "Aim"
                        });
                        _this.render();
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

        editPanelItem: function(item, items){
            var _this = this;
            var id = item.id;
            var title = "Edit " + item.type
            function onConfirm(name){
                if (item.type == "Challenge") {
                    var model = new GDSEModel({ id: id }, {
                        apiTag: 'challenges',
                        apiIds: [_this.caseStudy.id]
                    });
                } else {
                    var model = new GDSEModel({ id: id }, {
                        apiTag: 'aims',
                        apiIds: [_this.caseStudy.id]
                    });
                }

                model.save({
                    text: name
                }, {
                    success: function(){
                        var pos = items.map(function(e) {
                            return e.id;
                        }).indexOf(id);
                        items[pos].text = name;
                        _this.render();
                    }
                });
            }
            this.getName({
                name: item.text,
                title: gettext(title),
                onConfirm: onConfirm
            });
        },

        removePanelItem: function(item, items){
            var _this = this;
            var message = gettext("Do you want to delete the selected item?");
            this.confirmationModal.querySelector('.modal-body').innerHTML = message;
            $(this.confirmationModal).modal('show');
            if (item.type == "Challenge") {
                _this.model = new GDSEModel({ id: item.id }, {
                    apiTag: 'challenges',
                    apiIds: [_this.caseStudy.id]
                });
            } else {
                _this.model = new GDSEModel({ id: item.id }, {
                    apiTag: 'aims',
                    apiIds: [_this.caseStudy.id]
                });
            }
            _this.removeType = item.type;
        },

        confirmRemoval: function(items) {
            var _this = this;
            $(this.confirmationModal).modal('hide');
            var id = _this.model.get('id');
            _this.model.destroy({
                success: function(){
                    if (_this.removeType == "Challenge") {
                        var pos = _this.challenges.map(function(e) {
                            return e.id;
                        }).indexOf(id);
                        _this.challenges.splice(pos, 1);
                        _this.render();
                    } else {
                        var pos = _this.aims.map(function(e) {
                            return e.id;
                        }).indexOf(id);
                        _this.aims.splice(pos, 1);
                        _this.render();
                    }
                },
                error: _this.onError
            });
        },

    });
    return ChallengesAimsView;
}
);
