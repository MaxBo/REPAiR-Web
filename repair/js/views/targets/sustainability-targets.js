define(['underscore','views/common/baseview', 'collections/gdsecollection',
        'models/gdsemodel'],

function(_, BaseView, GDSECollection, GDSEModel){
    /**
    *
    * @author Christoph Franke
    * @name module:views/SustainabilityTargetsView
    * @augments Backbone.View
    */
    var SustainabilityTargetsView = BaseView.extend(
        /** @lends module:views/SustainabilityTargetsView.prototype */
        {

        /**
        * render workshop view on sustainability targets
        *
        * @param {Object} options
        * @param {HTMLElement} options.el                      element the view will be rendered in
        * @param {string} options.template                     id of the script element containing the underscore template to render this view
        * @param {module:models/CaseStudy} options.caseStudy   the casestudy to add targets to
        *
        * @constructs
        * @see http://backbonejs.org/#View
        */
        initialize: function(options){
            SustainabilityTargetsView.__super__.initialize.apply(this, [options]);
            var _this = this;

            this.template = options.template;
            this.caseStudy = options.caseStudy;
            this.keyflowId = options.keyflowId;
            this.keyflowName = options.keyflowName;
            this.aims = options.aims;
            this.userObjectives = options.userObjectives;
            this.targets = {};
            var promises = [];

            this.loader.activate();

            this.userObjectives.forEach(function(objective){
                var targets = new GDSECollection([], {
                    apiTag: 'sustainabilityTargets',
                    apiIds: [_this.caseStudy.id, objective.id]
                })
                _this.targets[objective.id] = targets;
                promises.push(targets.fetch({error: _this.onError}));
            })

            this.targetValues = new GDSECollection([], {
                apiTag: 'targetvalues',
            });

            this.areasOfProtection = new GDSECollection([], {
                apiTag: 'areasOfProtection',
            });

            promises.push(this.targetValues.fetch({error: _this.onError}))
            promises.push(this.areasOfProtection.fetch({error: _this.onError}))

            Promise.all(promises).then(function(){
                _this.loader.deactivate();
                _this.render();
            })

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
            this.el.innerHTML = template({
                keyflowName: this.keyflowName
            });
            this.objectivesPanel = document.createElement('div');
            this.el.appendChild(this.objectivesPanel);
            this.userObjectives.forEach(function(objective){
                _this.renderObjective(objective, _this.objectivesPanel);
            });
        },

        renderObjective: function(objective, panel){
            var _this = this,
                objectivePanel = document.createElement('div'),
                html = document.getElementById('sustainability-targets-detail-template').innerHTML,
                template = _.template(html),
                aim = this.aims.get(objective.get('aim')),
                targets = this.targets[objective.id].first();

            panel.appendChild(objectivePanel);
            objectivePanel.classList.add('objective-panel');
            objectivePanel.dataset['id'] = objective.id;

            objectivePanel.innerHTML = template({
                id: objective.id,
                title: aim.get('text')
            });

            objectivePanel.querySelector('.overlay').innerHTML = '#' + objective.get('priority');

            var btnGroup = objectivePanel.querySelector('.btn-group-toggle');

            this.areasOfProtection.forEach(function(aop){
                var label = document.createElement('label'),
                    input = document.createElement('input');
                label.classList.add('btn', 'btn-primary');
                label.innerHTML = aop.get('name');
                input.type = 'checkbox';
                input.checked = false;
                label.appendChild(input);
                btnGroup.appendChild(label);
            })
        },

        renderTargetRow: function(btnGroup, target, objective){
            this.areasOfProtection.forEach(function(aop){

            })
        },

        updateOrder(){
            var _this = this;
            // not ready yet (doesn't matter, order comes right after creation)
            if (!this.objectivesPanel) return;
            var objIds = this.userObjectives.pluck('id'),
                first = this.objectivesPanel.firstChild;
            objIds.reverse().forEach(function(id){
                var panel = _this.objectivesPanel.querySelector('.objective-panel[data-id="' + id + '"]');
                panel.querySelector('.overlay').innerHTML = '#' + _this.userObjectives.get(id).get('priority');
                _this.objectivesPanel.insertBefore(panel, first);
                first = panel;
            });
        }

    });
    return SustainabilityTargetsView;
}
);
