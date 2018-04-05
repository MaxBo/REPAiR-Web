define(['underscore','views/baseview', 'models/challenge', 'collections/challenges',
'models/aim', 'collections/aims'],

function(_, BaseView, Challenge, Challenges, Aim, Aims){
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
            var _this = this;
            _.bindAll(this, 'render');

            this.template = options.template;
            _this.caseStudy = options.caseStudy;
            this.mode = options.mode || 0;

            _this.challenges = [];
            this.challengesModel = new Challenges([], {
                caseStudyId: _this.caseStudy.id
            });
            _this.aims = [];
            this.aimsModel = new Aims([], {
                caseStudyId: _this.caseStudy.id
            });

            this.challengesModel.fetch({
                success: function(challenges){
                    _this.initItems(challenges, _this.challenges);
                    _this.render();
                },
                error: function(){
                    console.error("cannot fetch challenges");
                }
            });
            this.aimsModel.fetch({
                success: function(aims){
                    _this.initItems(aims, _this.aims);
                    _this.render();
                },
                error: function(){
                    console.error("cannot fetch aims");
                }
            });
        },

        /*
        * dom events (managed by jquery)
        */
        events: {
            'click #add-challenge-button': 'addChallenge',
            'click #add-aim-button': 'addAim'
        },

        initItems: function(items, list){
            items.forEach(function(item){
                list.push({
                    "text": item.get('text'),
                    "id": item.get('id')
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
                var challenge = new Challenge(
                    { text: text },
                    { caseStudyId: _this.caseStudy.id}
                );
                challenge.save(null, {
                    success: function(){
                        // var pos = _this.categories.map(function(e) {
                        //     return e.categoryId;
                        // }).indexOf(category.categoryId);
                        _this.challenges.push({
                            "text": challenge.get('text'),
                            "id": challenge.get('id')}
                        );
                        _this.render();
                    },
                    error: function(){
                        console.error("cannot save Challenge");
                    }
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
                var aim = new Aim(
                    { text: text },
                    { caseStudyId: _this.caseStudy.id}
                );
                aim.save(null, {
                    success: function(){
                        // var pos = _this.categories.map(function(e) {
                        //     return e.categoryId;
                        // }).indexOf(category.categoryId);
                        _this.aims.push({
                            "text": aim.get('text'),
                            "id": aim.get('id')}
                        );
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
            console.log("edit", item);
            console.log(items);
        },

        removePanelItem: function(item, items){
            console.log("remove", item);
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
    return ChallengesAimsView;
}
);
