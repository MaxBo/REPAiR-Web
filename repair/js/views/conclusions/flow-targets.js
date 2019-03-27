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

            this.targetValues = new GDSECollection([], {
                apiTag: 'targetvalues',
            });

            this.indicators = new GDSECollection([], {
                apiTag: 'flowIndicators',
                apiIds: [this.caseStudy.id, this.keyflowId],
                comparator: 'name'
            });

            var promises = [];
            this.loader.activate();
            promises.push(this.targetValues.fetch({error: _this.onError}))
            promises.push(this.indicators.fetch({error: _this.onError}))

            // stores targets {user1-id: {objective1-id: target-collection, objective2-id: target-collection, ...}, user2-id: ...}
            this.userTargetsPerIndicator = {};
            // stores count of indicators per aim {aim1-id: {indicator1-id: count, indicator2-id: count, ...}, aim2-id: ...}
            this.indicatorCountPerAim = {};
            this.maxIndCount = 0;
            this.users.forEach(function(user){
                var userObjectives = _this.objectives.filterBy({'user': user.get('user')});
                userObjectives.forEach(function(objective){
                    var targetsInObj = new GDSECollection([], {
                            apiTag: 'flowTargets',
                            apiIds: [_this.caseStudy.id, objective.id]
                        }),
                        aimId = objective.get('aim');
                    var indicatorCount = _this.indicatorCountPerAim[aimId];
                    if (!indicatorCount) indicatorCount = _this.indicatorCountPerAim[aimId] = {};
                    promises.push(targetsInObj.fetch({
                        success: function(){
                            // store used targets in set to avoid duplicates
                            var indUsed = new Set()
                            targetsInObj.forEach(function(target){
                                var indicatorId = target.get('indicator');
                                indUsed.add(indicatorId);
                                var targets = _this.userTargetsPerIndicator[indicatorId];
                                if (!targets) targets = _this.userTargetsPerIndicator[indicatorId] = {};
                                targets[user.id] = target;
                            })
                            indUsed.forEach(function(indicator){
                                if (!indicatorCount[indicator])
                                    indicatorCount[indicator] = 1;
                                else
                                    indicatorCount[indicator] += 1;
                                _this.maxIndCount = Math.max(_this.maxIndCount, indicatorCount[indicator])
                            })
                        },
                        error: _this.onError
                    }));
                })
            })

            Promise.all(promises).then(function(){
                _this.loader.deactivate();
                _this.indicators.sort();
                _this.render();
            })
        },
        /*
        * render the view
        */
        render: function(){
            EvalFlowTargetsView.__super__.render.call(this);
            this.renderIndicators();
            this.renderTargetValues();
        },

        // render Step 2
        renderIndicators: function(){
            var _this = this,
                table = this.el.querySelector('#indicator-table'),
                header = table.createTHead().insertRow(0),
                fTh = document.createElement('th');
            fTh.innerHTML = gettext('Objectives for key flow <i>' + this.keyflowName + '</i>');
            header.appendChild(fTh);

            var indicatorColumns = [];
            this.indicators.forEach(function(indicator){
                indicatorColumns.push(indicator.id)
                var th = document.createElement('th');
                th.innerHTML = indicator.get('name');
                header.appendChild(th);
            });

            var colorStep = 70 / this.maxIndCount;

            this.aims.forEach(function(aim){
                var row = table.insertRow(-1),
                    desc = aim.get('description') || '';
                var panelItem = _this.panelItem(aim.get('text'), {
                    popoverText: desc.replace(/\n/g, "<br/>")
                })
                panelItem.style.maxWidth = '500px';
                row.insertCell(0).appendChild(panelItem);
                var indicatorCount = _this.indicatorCountPerAim[aim.id];
                indicatorColumns.forEach(function(indicatorId){
                    var count = indicatorCount[indicatorId],
                        cell = row.insertCell(-1);
                    if (count){
                        var item = _this.panelItem(count + ' x');
                        item.style.width = '50px';
                        cell.appendChild(item);
                        var sat = 100 - colorStep * count,
                            hsl = 'hsla(90, 50%, ' + sat + '%, 1)';
                        if (sat < 50) item.style.color = 'white';
                        item.style.backgroundColor = hsl;
                    }
                })
            })

        },

        // render Step 3
        renderTargetValues: function(){
            var _this = this,
                table = this.el.querySelector('#target-values-table'),
                header = table.createTHead().insertRow(0),
                fTh = document.createElement('th');
            fTh.innerHTML = gettext('Indicators used as target setting in the key flow <i>' + this.keyflowName + '</i>');
            header.appendChild(fTh);

            var userColumns = [];
            this.users.forEach(function(user){
                userColumns.push(user.id);
                var name = user.get('alias') || user.get('name'),
                    th = document.createElement('th');
                th.innerHTML = name;
                header.appendChild(th.cloneNode(true));
            })
            this.indicators.forEach(function(indicator){
                var row = table.insertRow(-1),
                    text = indicator.get('name') + ' (' + indicator.get('spatial_reference').toLowerCase() + ')';
                var panelItem = _this.panelItem(text)
                panelItem.style.maxWidth = '500px';
                row.insertCell(0).appendChild(panelItem);
                var userTargets = _this.userTargetsPerIndicator[indicator.id];
                if (!userTargets) return;
                userColumns.forEach(function(userId){
                    var target = userTargets[userId],
                        cell = row.insertCell(-1);
                    if (target != null){
                        var targetValue = _this.targetValues.get(target.get('target_value')),
                            amount = targetValue.get('number'),
                            item = _this.panelItem(targetValue.get('text'));
                        cell.appendChild(item);
                        var hue = (amount >= 0) ? 90 : 0, // green or red
                            sat = 100 - 70 * Math.abs(Math.min(amount, 1)),
                            hsl = 'hsla(' + hue + ', 50%, ' + sat + '%, 1)';
                        if (sat < 50) item.style.color = 'white';
                        item.style.backgroundColor = hsl;
                    }
                })

            })
        },

    });
    return EvalFlowTargetsView;
}
);


