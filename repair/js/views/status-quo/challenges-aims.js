define(['backbone', 'underscore'],

function(Backbone, _,){
    /**
    *
    * @author Christoph Franke
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

            this.challenges = [
                'Recycling rate too low',
                'Missing facilities for treatment'
            ]
            this.aims = [
                'Higher Recycling rate',
                'Less non recyclable garbage'
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

            var challengesPanel = this.el.querySelector('#challenges').querySelector('.item-panel'),
                aimsPanel = this.el.querySelector('#aims').querySelector('.item-panel');
            this.renderPanel(challengesPanel, this.challenges);
            this.renderPanel(aimsPanel, this.aims);
        },

        renderPanel(panel, items){
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
    return ChallengesAimsView;
}
);