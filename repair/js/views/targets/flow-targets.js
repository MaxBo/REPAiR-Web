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
            this.targets = {};
            var promises = [];

            this.loader.activate();

            this.userObjectives.forEach(function(objective){
                var targets = new GDSECollection([], {
                    apiTag: 'flowTargets',
                    apiIds: [_this.caseStudy.id, objective.id]
                })
                _this.targets[objective.id] = targets;
                promises.push(targets.fetch({error: _this.onError}));
            })

            this.targetValues = new GDSECollection([], {
                apiTag: 'targetvalues',
            });

            this.indicators = new GDSECollection([], {
                apiTag: 'flowIndicators',
                apiIds: [this.caseStudy.id, this.keyflowId],
                comparator: 'name'
            });

            promises.push(this.targetValues.fetch({error: _this.onError}))
            promises.push(this.indicators.fetch({error: _this.onError}))

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
            this.userObjectives.forEach(this.renderObjective);
        },

        renderObjective: function(objective){
            var _this = this,
                el = document.createElement('div'),
                html = document.getElementById('flow-targets-detail-template').innerHTML,
                template = _.template(html),
                aim = this.aims.get(objective.get('aim')),
                targets = this.targets[objective.id];

            this.el.appendChild(el);
            el.innerHTML = template({
                id: objective.id,
                title: aim.get('text'),
                rank: objective.get('priority')
            });

            var addBtn = el.querySelector('button.add'),
                table = el.querySelector('.target-table');

            if (targets.length === 0)
                table.style.visibility = 'hidden';

            targets.forEach(function(target){
                _this.renderTargetRow(table, target, objective);
            })

            addBtn.addEventListener('click', function(){
                // just create a default Target
                var target = _this.targets[objective.id].create(
                    {
                        "indicator": _this.indicators.first().id,
                        "target_value": _this.targetValues.first().id,
                    },
                    {
                        wait: true,
                        success: function(){
                            table.style.visibility = 'visible';
                            _this.renderTargetRow(table, target, objective);
                        },
                        error: _this.onError
                    }
                );
            })
        },

        renderTargetRow: function(table, target, objective){
            var _this = this,
                row = table.insertRow(-1),
                indicatorSelect = document.createElement('select'),
                spatialDiv = document.createElement('div'),
                targetSelect = document.createElement('select'),
                removeBtn = document.createElement('button');

            indicatorSelect.classList.add('form-control');
            targetSelect.classList.add('form-control');


            removeBtn.classList.add("btn", "btn-warning", "square", "remove");
            // removeBtn.style.float = 'right';
            var span = document.createElement('span');
            removeBtn.title = gettext('Remove target')
            span.classList.add('glyphicon', 'glyphicon-minus');
            span.style.pointerEvents = 'none';
            removeBtn.appendChild(span);

            removeBtn.addEventListener('click', function(){
                target.destroy({ success: function(){
                    table.deleteRow(row.rowIndex);
                }})
            })

            this.indicators.forEach(function(indicator){
                var option = document.createElement('option');
                option.value = indicator.id;
                option.innerHTML = indicator.get('name');
                indicatorSelect.appendChild(option);
            });
            indicatorSelect.value = target.get('indicator');

            this.targetValues.forEach(function(value){
                var option = document.createElement('option');
                option.value = value.id;
                option.innerHTML = value.get('text');
                targetSelect.appendChild(option);
            });
            targetSelect.value = target.get('target_value');

            indicatorSelect.addEventListener('change', function(){
                target.save(
                    { indicator: this.value },
                    { patch: true, error: _this.onError }
                )
            })

            targetSelect.addEventListener('change', function(){
                target.save(
                    { target_value: this.value },
                    { patch: true, error: _this.onError }
                )
            })

            row.insertCell(-1).appendChild(indicatorSelect);
            row.insertCell(-1).appendChild(spatialDiv);
            row.insertCell(-1).appendChild(targetSelect);
            row.insertCell(-1).appendChild(removeBtn);

        }

    });
    return FlowTargetsView;
}
);

