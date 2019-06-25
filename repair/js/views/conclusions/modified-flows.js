
define(['underscore','views/common/baseview', 'collections/gdsecollection',
        'visualizations/barchart'],

function(_, BaseView, GDSECollection, BarChart){
    /**
    *
    * @author Christoph Franke
    * @name module:views/EvalModifiedFlowsView
    * @augments Backbone.View
    */
    var EvalModifiedFlowsView = BaseView.extend(
        /** @lends module:views/EvalModifiedFlowsView.prototype */
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
            EvalModifiedFlowsView.__super__.initialize.apply(this, [options]);
            var _this = this;
            this.template = options.template;
            this.caseStudy = options.caseStudy;
            this.keyflowId = options.keyflowId;
            this.keyflowName = options.keyflowName;
            this.users = options.users;
            this.strategies = options.strategies;
            this.indicators = options.indicators;
            this.objectives = options.objectives;

            this.loader.activate();
            promises = [];

            this.targetValues = new GDSECollection([], {
                apiTag: 'targetvalues',
            });
            promises.push(this.targetValues.fetch({error: _this.onError}));

            this.indicatorValues = {};
            var csJSON = JSON.stringify(this.caseStudy.get('geometry')),
                fJSON = JSON.stringify(this.caseStudy.get('properties').focusarea);

            this.indicators.forEach(function(indicator){
                _this.indicatorValues[indicator.id] = {};
                var spatialRef = indicator.get('spatial_reference');
                _this.users.forEach(function(user){
                    var strategies = _this.strategies.where({user: user.id});
                    if (strategies.length == 0) return;
                    var strategy = strategies[0];
                    if (strategy.get('status') != 2) return;
                    promises.push(
                        indicator.compute({
                            method: "POST",
                            data: {
                                geom: (spatialRef == 'REGION') ? csJSON : fJSON,
                                strategy: strategy.id
                            },
                            success: function(data){
                                var data = data[0],
                                    strategyValue = data.value;
                                    deltaValue = data.delta || 0,
                                    isAbs = indicator.get('is_absolute'),
                                    statusquoValue = strategyValue - deltaValue;
                                // ToDo: what if no status quo?
                                if (!statusquoValue) return;
                                _this.indicatorValues[indicator.id][user.id] = data;
                                data.deltaPerc = (isAbs) ? deltaValue / statusquoValue * 100 : deltaValue;
                            },
                            error: _this.onError
                        })
                    )
                })
            })
            this.userTargetsPerIndicator = {};
            this.users.forEach(function(user){
                var userObjectives = _this.objectives.where({'user': user.get('user')});
                userObjectives.forEach(function(objective){
                    var aimId = objective.get('aim');
                    objective.targets.forEach(function(target){
                        var indicatorId = target.get('indicator'),
                            targets = _this.userTargetsPerIndicator[indicatorId];
                        if (!targets) targets = _this.userTargetsPerIndicator[indicatorId] = {};
                        targets[user.id] = target;
                    })
                })
            })

            function render(){
                _this.loader.deactivate();
                _this.render();
            }
            // render even on error (happening when some calculations are not ready)
            Promise.all(promises).then(render);
        },
        /*
        * render the view
        */
        render: function(){
            EvalModifiedFlowsView.__super__.render.call(this);
            this.renderIndicators();
            this.renderComparison();
        },

        // render Step 8
        renderIndicators: function(){
            var _this = this,
                table = this.el.querySelector('table[name="indicator-table"]'),
                header = table.createTHead().insertRow(0),
                fTh = document.createElement('th');
            fTh.innerHTML = gettext('Flow indicators for key flow <i>' + this.keyflowName + '</i>');
            header.appendChild(fTh);

            var userColumns = [];
            this.users.forEach(function(user){
                userColumns.push(user.id);
                var name = user.get('alias') || user.get('name'),
                    th = document.createElement('th');
                th.innerHTML = name;
                header.appendChild(th.cloneNode(true));
            })

            var colorStep = 70 / this.maxIndCount;
            this.indicators.forEach(function(indicator){
                var row = table.insertRow(-1),
                    text = indicator.get('name') + ' (' + indicator.get('spatial_reference').toLowerCase() + ')';
                var panelItem = _this.panelItem(text);
                panelItem.style.maxWidth = '500px';
                row.insertCell(0).appendChild(panelItem);
                userColumns.forEach(function(userId){
                    var cell = row.insertCell(-1),
                        data = _this.indicatorValues[indicator.id][userId];
                    if (!data) return;
                    var unit = indicator.get('unit'),
                        dt = (data.deltaPerc > 0) ? '+' + _this.format(data.deltaPerc) : _this.format(data.deltaPerc);
                        item = _this.panelItem(dt + '%');
                    cell.appendChild(item);
                    var hue = (data.deltaPerc >= 0) ? 90 : 0, // green or red
                        sat = 100 - 70 * Math.abs(Math.min(data.deltaPerc / 100, 1)),
                        hsl = 'hsla(' + hue + ', 50%, ' + sat + '%, 1)';
                    if (sat < 50) item.style.color = 'white';
                    item.style.backgroundImage = 'none';
                    item.style.backgroundColor = hsl;
                })
            })
        },

        // render Step 8
        renderComparison: function(){
            var _this = this,
                table = this.el.querySelector('table[name="comparison-table"]'),
                header = table.createTHead().insertRow(0),
                fTh = document.createElement('th'),
                sTh = document.createElement('th');
            fTh.innerHTML = gettext('Flow indicators for key flow <i>' + this.keyflowName + '</i>');
            sTh.innerHTML = gettext('Status');
            header.appendChild(fTh);
            header.appendChild(sTh);

            var chartWidth = _this.users.length * 150,
                userTh = document.createElement('th');
            userTh.style.minWidth = chartWidth + 50 + 'px';
            header.appendChild(userTh);
            var userStatus = {};

            this.indicators.forEach(function(indicator){
                var row = table.insertRow(-1),
                    text = indicator.get('name') + ' (' + indicator.get('spatial_reference').toLowerCase() + ')';
                var panelItem = _this.panelItem(text)
                panelItem.style.maxWidth = '500px';
                row.insertCell(0).appendChild(panelItem);

                var statusCell = row.insertCell(-1),
                    userTargets = _this.userTargetsPerIndicator[indicator.id];
                    chartData = [],
                    chartCell = row.insertCell(-1),
                    indTargetCount = 0,
                    indAchievedCount = 0;
                _this.users.forEach(function(user){
                    var data = _this.indicatorValues[indicator.id][user.id],
                        target = (userTargets) ? userTargets[user.id] : null,
                        targetValue = (target) ? _this.targetValues.get(target.get('target_value')) : null,
                        targetPerc = (targetValue) ? targetValue.get('number') * 100 : 0,
                        targetText = (targetValue) ? targetValue.get('text') : null,
                        deltaPerc = (data) ? data.deltaPerc : 0,
                        dt = (deltaPerc > 0) ? '+' + _this.format(deltaPerc) : _this.format(deltaPerc);

                    chartData.push({
                        group: user.get('name'),
                        values: [
                            { name: gettext('Strategy'), text: dt + '%', value: deltaPerc, color: '#4a8ef9' },
                            { name: gettext('Target'), text: targetText, value: targetPerc, color: '#cecece' }
                        ]
                    })

                    var userStat = userStatus[user.id];
                    if (!userStat) userStat = userStatus[user.id] = { targetCount: 0, achievedCount: 0 };
                    if (target){
                        userStat.targetCount += 1;
                        indTargetCount += 1;
                        // target achieved
                        if ((targetPerc < 0 && deltaPerc <= targetPerc) || (targetPerc > 0 && deltaPerc >= targetPerc)) {
                            indAchievedCount += 1;
                            userStat.achievedCount += 1;
                        }
                    }
                });

                var item = _this.panelItem(indAchievedCount + '/' + indTargetCount);
                statusCell.appendChild(item);
                var sat = 100 - 70 * indAchievedCount/indTargetCount,
                    hsl = 'hsla( 90 , 50%, ' + sat + '%, 1)';
                if (sat < 50) item.style.color = 'white';
                item.style.backgroundImage = 'none';
                item.style.backgroundColor = hsl;

                var barChart = new BarChart({
                    el: chartCell,
                    width: chartWidth,
                    height: 50,
                    margin: { left: 0, right: 0, bottom: 0, top: 0 },
                    grouped: true,
                    hideLabels: true
                })
                barChart.draw(chartData);
                barChart.svg.style.float = 'left';
            })

            this.users.forEach(function(user){
                var userDiv = document.createElement('div'),
                    name = user.get('alias') || user.get('name');
                userDiv.style.width = '150px';
                userDiv.style.float = 'left';
                var status = userStatus[user.id]
                userDiv.innerHTML = name + ' (' + status.achievedCount + '/' + status.targetCount + ')';
                userTh.appendChild(userDiv);
            });
        }
    });
    return EvalModifiedFlowsView;
}
);

