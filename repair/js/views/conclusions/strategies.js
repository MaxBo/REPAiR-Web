
define(['underscore','views/common/baseview', 'collections/gdsecollection'],

function(_, BaseView, GDSECollection, Muuri){
    /**
    *
    * @author Christoph Franke
    * @name module:views/EvalStrategiesView
    * @augments Backbone.View
    */
    var EvalStrategiesView = BaseView.extend(
        /** @lends module:views/EvalStrategiesView.prototype */
    {

        /**
        * render workshop view on overall objective-ranking by involved users
        *
        * @param {Object} options
        * @param {HTMLElement} options.el                      element the view will be rendered in
        * @param {string} options.template                     id of the script element containing the underscore template to render this view
        * @param {module:models/CaseStudy} options.caseStudy   the casestudy of the keyflow
        * @param {module:models/CaseStudy} options.keyflowId   the keyflow the objectives belong to
        *
        * @constructs
        * @see http://backbonejs.org/#View
        */
        initialize: function(options){
            EvalStrategiesView.__super__.initialize.apply(this, [options]);
            var _this = this;
            this.template = options.template;
            this.caseStudy = options.caseStudy;
            this.aims = options.aims;
            this.objectives = options.objectives;
            this.keyflowId = options.keyflowId;
            this.keyflowName = options.keyflowName;
            this.users = options.users;

            // ToDo: non-keyflow related collections obviously don't change when changing keyflow
            // so general collections could be already fetched outside, no performance issues expected though
            this.generalAims = new GDSECollection([], {
                apiTag: 'aims',
                apiIds: [this.caseStudy.id]
            });
            this.generalObjectives = new GDSECollection([], {
                apiTag: 'userObjectives',
                apiIds: [this.caseStudy.id]
            });
            this.loader.activate();
            promises = [];
            var data = { 'keyflow__isnull': true }
            promises.push(this.generalAims.fetch({ data: data, error: this.onError }));
            promises.push(this.generalObjectives.fetch({ data: data, error: this.onError }));
            Promise.all(promises).then(function(){
                _this.loader.deactivate();
                _this.render();
            });
        },
        /*
        * render the view
        */
        render: function(){
            EvalObjectivesView.__super__.render.call(this);
        },
    });
    return EvalStrategiesView;
}
);

