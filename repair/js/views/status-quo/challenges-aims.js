define(['backbone', 'underscore', 'models/challenge', 'collections/challenges',
'models/aim', 'collections/aims'],

function(Backbone, _, Challenge, Challenges, Aim, Aims){
    /**
    *
    * @author Christoph Franke, Balázs Dukai
    * @name module:views/ChallengesAimsView
    * @augments Backbone.View
    */
    var ChallengesAimsView = Backbone.View.extend(
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
            this.caseStudy = options.caseStudy;
            var caseStudyId = this.caseStudy.id;
            this.mode = options.mode || 0;

            // this.challenges = [
            //     'Recycling rate too low',
            //     'Missing facilities for treatment'
            // ]
            this.challenges = new Challenges([], {
                caseStudyId: caseStudyId
            });
            this.aims = new Aims([], {
                caseStudyId: caseStudyId
            });

            this.challenges.fetch({
                success: function(challenges){
                    challenges.forEach(function(challenge){
                        console.log(challenge);
                        var text = challenge.get('text');
                        console.log(text);
                    });
                },
                error: function(){
                    console.error("cannot fetch challenges");
                }
            })
            this.aims.fetch({
                success: function(aims){
                    aims.forEach(function(aim){
                        console.log(aim);
                        var text = aim.get('text');
                        console.log(text);
                    });
                },
                error: function(){
                    console.error("cannot fetch aims");
                }
            })

            this.render();
        },

        /*
        * dom events (managed by jquery)
        */
        events: {
            'click #add-challenge-button': 'addChallenge',
            'click #add-aim-button': 'addAim'
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
                panelItem.innerHTML = template({ name: item });
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
            })
        },

        addChallenge: function(){
            alert("add challenge");
        },

        addAim: function(){
            alert("add aim");
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
