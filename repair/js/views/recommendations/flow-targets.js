
define(['underscore','views/common/baseview', 'collections/gdsecollection'],

function(_, BaseView, GDSECollection, Muuri){
    /**
    *
    * @author Christoph Franke
    * @name module:views/EvalFlowTargetsView
    * @augments Backbone.View
    */
    var EvalFlowTargetsView = BaseView.extend(
        /** @lends module:views/EvalFlowTargetsView.prototype */
    {

        /**
        * render evaluation of flow targets set by involved users
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
            EvalFlowTargetsView.__super__.initialize.apply(this, [options]);
            var _this = this;
            this.template = options.template;
            this.caseStudy = options.caseStudy;
            this.aims = options.aims;
            this.objectives = options.objectives;
            this.keyflowId = options.keyflowId;
            this.keyflowName = options.keyflowName;
            this.users = options.users;

            this.render();
        },
        /*
        * render the view
        */
        render: function(){
            EvalFlowTargetsView.__super__.render.call(this);
            this.indicatorTable = this.el.querySelector('#indicator-table');
            this.targetValuesTable = this.el.querySelector('#target-values-table');

            var _this = this;
                indicatorHeader = this.indicatorTable.createTHead().insertRow(0),
                targetValuesHeader = this.targetValuesTable.createTHead().insertRow(0);

            var fTh = document.createElement('th');
            fTh.style.width = '1%';
            fTh.innerHTML = gettext('Objectives for key flow <i>' + this.keyflowName + '</i>');
            indicatorHeader.appendChild(fTh);
            fTh = document.createElement('th');
            fTh.style.width = '1%';
            fTh.innerHTML = gettext('Flow indicators used by at least one participant / small group for target setting on the key flow <i>' + this.keyflowName + '</i>');
            targetValuesHeader.appendChild(fTh);

            this.userColumns = [];
            this.users.forEach(function(user){
                _this.userColumns.push(user.id);
                var name = user.get('alias') || user.get('name'),
                    th = document.createElement('th');
                th.innerHTML = name;
                th.style.width = '1%';
                indicatorHeader.appendChild(th);
                targetValuesHeader.appendChild(th.cloneNode(true));
            })

            this.renderIndicators();
        },

        renderIndicators: function(){

        },

        renderTargetValues: function(){

        },
    });
    return EvalFlowTargetsView;
}
);


