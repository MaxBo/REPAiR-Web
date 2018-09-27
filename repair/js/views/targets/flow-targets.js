define(['underscore','views/common/baseview', 'collections/gdsecollection',
        'models/gdsemodel'],

function(_, BaseView, GDSECollection, GDSEModel){
    /**
    *
    * @author Christoph Franke
    * @name module:views/FlowTargetsView
    * @augments Backbone.View
    */
    var FlowTargetsView = BaseView.extend(
        /** @lends module:views/FlowTargetsView.prototype */
        {

        /**
        * render workshop view on flow targets
        *
        * @param {Object} options
        * @param {HTMLElement} options.el                      element the view will be rendered in
        * @param {string} options.template                     id of the script element containing the underscore template to render this view
        * @param {module:models/CaseStudy} options.caseStudy   the casestudy of the keyflow
        * @param {module:models/CaseStudy} options.keyflowId   id of the keyflow to add targets to
        *
        * @constructs
        * @see http://backbonejs.org/#View
        */
        initialize: function(options){
            FlowTargetsView.__super__.initialize.apply(this, [options]);
            var _this = this;
            _.bindAll(this, 'renderObjective');

            this.template = options.template;
            this.caseStudy = options.caseStudy;
            this.keyflowId = options.keyflowId;
            this.keyflowName = options.keyflowName;
            this.aims = options.aims;
            this.userObjectives = options.userObjectives;

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
            var _this = this,
                html = document.getElementById(this.template).innerHTML,
                template = _.template(html);
            this.el.innerHTML = template({ keyflowName: this.keyflowName });
            this.userObjectives.forEach(this.renderObjective)
        },

        renderObjective: function(objective){
            var el = document.createElement('div'),
                html = document.getElementById('flow-targets-detail-template').innerHTML,
                template = _.template(html),
                _this = this;

            var aim = this.aims.get(objective.get('aim'));

            this.el.appendChild(el);
            el.innerHTML = template({ id: objective.id, title: aim.get('text') });
        }

    });
    return FlowTargetsView;
}
);

