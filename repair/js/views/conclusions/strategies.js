
define(['underscore','views/common/baseview', 'collections/gdsecollection',
        'visualizations/map', 'openlayers', 'chroma-js'],

function(_, BaseView, GDSECollection, Map, ol, chroma){
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
        * render workshop view on strategies implemented by users
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
            this.keyflowId = options.keyflowId;
            this.keyflowName = options.keyflowName;
            this.users = options.users;

            this.solutions = new GDSECollection([], {
                apiTag: 'solutions',
                apiIds: [this.caseStudy.id, this.keyflowId],
                comparator: 'implementation_count'
            });
            this.strategies = options.strategies;
            this.stakeholderCategories = new GDSECollection([], {
                apiTag: 'stakeholderCategories',
                apiIds: [this.caseStudy.id]
            });
            this.activities = new GDSECollection([], {
                apiTag: 'activities',
                apiIds: [this.caseStudy.id, this.keyflowId],
                comparator: 'name'
            });
            this.activityGroups = new GDSECollection([], {
                apiTag: 'activitygroups',
                apiIds: [this.caseStudy.id, this.keyflowId],
                comparator: 'name'
            });

            promises = [];

            promises.push(this.stakeholderCategories.fetch({ error: this.onError }));
            promises.push(this.solutions.fetch({ error: this.onError }));
            promises.push(this.stakeholderCategories.fetch({ error: this.onError }))
            promises.push(this.activities.fetch({ error: this.onError }))
            promises.push(this.activityGroups.fetch({ error: this.onError }))
            this.implementations = {};
            this.strategies.forEach(function(strategy){
                var implementations = new GDSECollection([], {
                    apiTag: 'solutionsInStrategy',
                    apiIds: [_this.caseStudy.id, _this.keyflowId, strategy.id]
                });
                promises.push(implementations.fetch({
                    success: function (){
                        _this.implementations[strategy.id] = implementations;
                    },
                    error: _this.onError
                }));
            })
            this.stakeholders = {};
            this.questions = {};
            this.loader.activate();
            Promise.all(promises).then(function(){
                var promises = [];
                _this.stakeholderCategories.forEach(function(category){
                    var stakeholders = new GDSECollection([], {
                        apiTag: 'stakeholders',
                        apiIds: [_this.caseStudy.id, category.id]
                    });

                    promises.push(stakeholders.fetch({
                        success: function (){
                            _this.stakeholders[category.id] = stakeholders;
                            stakeholders.sort();
                        },
                        error: _this.onError
                    }));
                })
                _this.solutions.sort();
                _this.solutions.models.reverse();
                _this.solutions.forEach(function(solution){
                    var questions = new GDSECollection([], {
                        apiTag: 'questions',
                        apiIds: [_this.caseStudy.id, _this.keyflowId, solution.id]
                    });
                    promises.push(questions.fetch({
                        success: function (){
                            _this.questions[solution.id] = questions;
                        },
                        error: _this.onError
                    }));
                })
                Promise.all(promises).then(function(){
                    _this.loader.deactivate();
                    _this.render();
                })
            });
        },

        events: {
            'change select[name="level-select"]': 'renderAffectedGroups',
            'change select[name="solutions"]': 'drawImplementations'
        },

        /*
        * render the view
        */
        render: function(){
            var html = document.getElementById(this.template).innerHTML,
                template = _.template(html),
                _this = this;
            this.el.innerHTML = template({ solutions: this.solutions });
            this.solutionSelect = this.el.querySelector('select[name="solutions"]')
            this.elLegend = this.el.querySelector('.legend');
            this.setupUsers();
            // step 4
            this.renderQuestions();
            // step 5
            this.setupStrategiesMap();
            // step 6
            this.renderAffectedGroups();
            // step 7
            this.stakeholderCategories.forEach(function(category){
                _this.renderStakeholders(category);
            })
        },

        setupUsers: function(){
            var colorRange = chroma.scale(['red', 'yellow', 'blue', 'violet']),
                colorDomain = colorRange.domain([0, this.users.size()]),
                _this = this;
            // color for user on map
            this.userColors = {};
            // count per stakeholder and user
            this.stakeholderCount = {};
            // set of users per activity
            this.directlyAffectedActivities = {};
            this.indirectlyAffectedActivities = {};
            // set of users per activity group
            this.directlyAffectedGroups = {};
            this.indirectlyAffectedGroups = {};

            // quantity values per user and question
            this.quantities = {};
            var i = 0;
            this.users.forEach(function(user){

                // implementation areas
                var color = colorDomain(i).hex(),
                    square = document.createElement('div'),
                    label = document.createElement('label');
                square.style.height = '25px';
                square.style.width = '50px';
                square.style.float = 'left';
                square.style.backgroundColor = color;
                square.style.marginRight = '5px';
                label.innerHTML = user.get('alias') || user.get('name');
                _this.elLegend.appendChild(square);
                _this.elLegend.appendChild(label);
                _this.elLegend.appendChild(document.createElement('br'));

                _this.userColors[user.id] = color;
                i++;

                // stakeholder per strategy count
                var strategies = _this.strategies.where({user: user.id});
                // should actually not happen since every user has a auto created strategy
                if(strategies.length == 0) return;
                var strategy = strategies[0],
                    implementations = _this.implementations[strategy.id];

                // information related to implementations by users (aka solution in strategy)
                implementations.forEach(function(implementation){
                    var solution = _this.solutions.get(implementation.get('solution'));
                    // workaround for incorrect implementations in backend
                    if (!solution) return;
                    // count stakeholders assigned by users
                    implementation.get('participants').forEach(function(stakeholderId){
                        if (!_this.stakeholderCount[stakeholderId])
                            _this.stakeholderCount[stakeholderId] = {};
                        if (!_this.stakeholderCount[stakeholderId][user.id])
                            _this.stakeholderCount[stakeholderId][user.id] = {
                                'count': 0,
                                'solutions': []
                            };
                        _this.stakeholderCount[stakeholderId][user.id]['count'] += 1;
                        _this.stakeholderCount[stakeholderId][user.id]['solutions'].push('<li>' + solution.get('name') + '</li>');
                    })
                    // memorize quantity inputs by users
                    implementation.get('quantities').forEach(function(quantity){
                        if (!_this.quantities[user.id]) _this.quantities[user.id] = {};
                        if (!_this.quantities[user.id][quantity.question])
                            _this.quantities[user.id][quantity.question] = [];
                        _this.quantities[user.id][quantity.question].push(quantity.value);
                    });
                    // memorize activities directly affected by user strategies
                    solution.get('affected_activities').forEach(function(activityId){
                        var users = _this.directlyAffectedActivities[activityId];
                        if (!users)
                            users = _this.directlyAffectedActivities[activityId] = new Set();
                        users.add(user.id);
                        var activity = _this.activities.get(activityId),
                            groupId = activity.get('activitygroup');
                        users = _this.directlyAffectedGroups[groupId];
                        if (!users)
                            users = _this.directlyAffectedGroups[groupId] = new Set();
                        users.add(user.id);
                    })
                })
                // memorize activities indirectly affected by user strategies
                strategy.get('affected_activities').forEach(function(activityId){
                    var users = _this.indirectlyAffectedActivities[activityId];
                    if (!users)
                        users = _this.indirectlyAffectedActivities[activityId] = new Set();
                    users.add(user.id);
                    var activity = _this.activities.get(activityId),
                        groupId = activity.get('activitygroup');
                    users = _this.indirectlyAffectedGroups[groupId];
                    if (!users)
                        users = _this.indirectlyAffectedGroups[groupId] = new Set();
                    users.add(user.id);
                })
            })
            // sum up stakeholder counts
            this.maxStakeholderCount = 0;
            for (var stakeholderId in this.stakeholderCount) {
                var total = 0,
                    solutions = [];
                Object.values(this.stakeholderCount[stakeholderId]).forEach(function(count){
                    total += count['count'];
                    solutions = solutions.concat(count['solutions']);
                })
                this.stakeholderCount[stakeholderId]['total'] = {
                    'count': total,
                    'solutions': [...new Set(solutions)]
                };
                this.maxStakeholderCount = Math.max(this.maxStakeholderCount, total);
            }
            // sum up directly affected activities
            for (var activityId in _this.directlyAffectedActivities) {
                var count = _this.directlyAffectedActivities[activityId].size,
                    activity = _this.activities.get(activityId);
                activity.set('directlyAffectedCount', count);
            }
            // sum up indirectly affected activities
            for (var activityId in _this.indirectlyAffectedActivities) {
                var count = _this.indirectlyAffectedActivities[activityId].size,
                    activity = _this.activities.get(activityId);
                activity.set('indirectlyAffectedCount', count);
            }
            // sum up directly affected groups
            for (var groupId in _this.directlyAffectedGroups) {
                var count = _this.directlyAffectedGroups[groupId].size,
                    group = _this.activityGroups.get(groupId);
                group.set('directlyAffectedCount', count);
            }
            // sum up indirectly affected groups
            for (var groupId in _this.indirectlyAffectedGroups) {
                var count = _this.indirectlyAffectedGroups[groupId].size,
                    group = _this.activityGroups.get(groupId);
                group.set('indirectlyAffectedCount', count);
            }
        },

        setupStrategiesMap: function(){
            var _this = this;
            this.strategiesMap = new Map({
                el: this.el.querySelector('#strategies-map'),
                opacity: 0.8
            });
            this.users.forEach(function(user){
                var color = _this.userColors[user.id];
                _this.strategiesMap.addLayer('user' + user.id, {
                    stroke: color,
                    fill: color,
                    opacity: 0.7,
                    strokeWidth: 1,
                    zIndex: 998
                });
            })
        },

        // Step 5
        drawImplementations: function(){
            var solution = this.solutions.get(this.solutionSelect.value),
                possImplArea = solution.get('possible_implementation_area'),
                focusarea = this.caseStudy.get('properties').focusarea,
                _this = this;

            if (possImplArea) {
                var poly = new ol.geom.MultiPolygon(possImplArea.coordinates);
                this.strategiesMap.centerOnPolygon(poly, { projection: this.projection });
            } else if (focusarea){
                var poly = new ol.geom.MultiPolygon(focusarea.coordinates);
                this.strategiesMap.centerOnPolygon(poly, { projection: this.projection });
            };

            this.users.forEach(function(user){
                _this.strategiesMap.clearLayer('user' + user.id);
                var strategies = _this.strategies.where({user: user.id});
                // should actually not happen since every user has a auto created strategy
                if(strategies.length == 0) return;
                var strategy = strategies[0],
                    implementations = _this.implementations[strategy.id].where({solution: solution.id}),
                    userName = user.get('alias') || user.get('name');
                implementations.forEach(function(solutionImpl){
                    var implAreas = solutionImpl.get('geom');
                    // implementation areas are collections
                    if (!implAreas || implAreas.geometries.length == 0) return;
                    implAreas.geometries.forEach(function(geom){
                        _this.strategiesMap.addGeometry(geom.coordinates, {
                            projection: 'EPSG:3857',
                            layername: 'user' + user.id,
                            type: geom.type,
                            tooltip: userName
                        });
                    })
                })
            });
        },

        // Step 4
        renderQuestions: function(){
            var _this = this,
                table = this.el.querySelector('#solution-question-table'),
                header = table.createTHead().insertRow(0),
                fTh = document.createElement('th');
            fTh.innerHTML = gettext('Solutions for key flow <i>' + this.keyflowName + '</i>');
            header.appendChild(fTh);
            var userColumns = [];
            this.users.forEach(function(user){
                userColumns.push(user.id);
                var name = user.get('alias') || user.get('name'),
                    th = document.createElement('th');
                th.innerHTML = name;
                header.appendChild(th);
            })

            //var colorStep = 70 / this.maxStakeholderCount;

            function renderItem(count, cell){
                var item = _this.panelItem(count + ' x');
                item.style.backgroundImage = 'none';
                item.style.width = '50px';
                cell.appendChild(item);
                var sat = 100 - colorStep * count,
                    hsl = 'hsla(90, 50%, ' + sat + '%, 1)';
                if (sat < 50) item.style.color = 'white';
                item.style.backgroundColor = hsl;
            }

            this.solutions.forEach(function(solution){
                var row = table.insertRow(-1),
                    text = solution.get('name'),
                    questions = _this.questions[solution.id];
                var solItem = _this.panelItem(text, { overlayText: '0x' });
                solItem.style.maxWidth = '600px';
                row.insertCell(0).appendChild(solItem);
                _this.users.forEach(function(user){
                    // insert empty cells so that the lines are drawn
                    row.insertCell(-1);
                });
                solItem.querySelector('.overlay').innerHTML = solution.get('implementation_count') + 'x';
                questions.forEach(function(question){
                    var qrow = table.insertRow(-1),
                        panelItem = _this.panelItem(question.get('question'));
                    panelItem.style.maxWidth = '400px';
                    panelItem.style.marginLeft = '200px';
                    panelItem.style.backgroundImage = 'none';
                    panelItem.style.pointerEvents = 'none';
                    var cell = qrow.insertCell(0);
                    cell.style.border = '0px';
                    cell.appendChild(panelItem);
                    _this.users.forEach(function(user){
                        var cell = qrow.insertCell(-1);
                        if (!_this.quantities[user.id]) return;
                        var values = _this.quantities[user.id][question.id],
                            isAbsolute = question.get('is_absolute');
                        values.forEach(function(value){
                            var v = (isAbsolute) ? value + ' ' + gettext('t/year') : parseFloat(value) * 100 + '%',
                                t = '<b>' + (user.get('alias') || user.get('name')) + '</b><br><i>' + question.get('question') + '</i>:<br>' + v,
                                panelItem = _this.panelItem(v, { popoverText: t });
                            panelItem.style.float = 'left';
                            cell.appendChild(panelItem);
                        })
                    });
                });
            })
        },

        // Step 6
        renderAffectedGroups: function(){
            var _this = this,
                directTable = this.el.querySelector('#directly-affected-table'),
                indirectTable = this.el.querySelector('#indirectly-affected-table');
            // clear tables
            while(directTable.hasChildNodes()) { directTable.removeChild(directTable.firstChild); }
            while(indirectTable.hasChildNodes()) { indirectTable.removeChild(indirectTable.firstChild); }

            var directHeader = directTable.createTHead().insertRow(0),
                indirectHeader = indirectTable.createTHead().insertRow(0),
                fTh = document.createElement('th'),
                ifTh = document.createElement('th'),
                levelSelect = this.el.querySelector('select[name="level-select"]'),
                gName = (levelSelect.value == 'activity') ? 'Activities' : 'Activity groups';
            fTh.innerHTML = gName + ' ' + gettext('directly affected by user strategies <br> in key flow <i>' + this.keyflowName + '</i>');
            ifTh.innerHTML = gName + ' ' + gettext('indirectly affected by user strategies <br> in key flow <i>' + this.keyflowName + '</i>');
            directHeader.appendChild(fTh);
            indirectHeader.appendChild(ifTh);
            var userColumns = [];
            this.users.forEach(function(user){
                userColumns.push(user.id);
                var name = user.get('alias') || user.get('name'),
                    th = document.createElement('th');
                th.innerHTML = name;
                directHeader.appendChild(th.cloneNode(true));
                indirectHeader.appendChild(th.cloneNode(true));
            })
            var glyphicon = '<span class="glyphicon glyphicon-ok"></span>';

            function addRow(table, node, userSet, totalCount){
                var row = table.insertRow(-1),
                    text = node.get('name');
                var panelItem = _this.panelItem(text, { overlayText: totalCount + 'x' });
                panelItem.style.width = '500px';
                row.insertCell(0).appendChild(panelItem);
                _this.users.forEach(function(user){
                    var cell = row.insertCell(-1);
                    if (!userSet.has(user.id)) return;
                    var panelItem = _this.panelItem(glyphicon,
                        { popoverText: '<b>' + (user.get('alias') || user.get('name')) + '</b><br>' + gettext('strategy affects') + '<br><i>' + node.get('name') + '</i>' }
                    );
                    panelItem.style.backgroundImage = 'none';
                    panelItem.style.width = '50px';
                    cell.appendChild(panelItem);
                    cell.appendChild(panelItem);
                });
            }

            if (levelSelect.value == 'activity'){
                this.activities.comparatorAttr = 'directlyAffectedCount';
                this.activities.sort();
                this.activities.forEach(function(activity){
                    var count = activity.get('directlyAffectedCount');
                    if (!count) return;
                    addRow(directTable, activity, _this.directlyAffectedActivities[activity.id], count)
                })

                this.activities.comparatorAttr = 'indirectlyAffectedCount';
                this.activities.sort();
                this.activities.forEach(function(activity){
                    var count = activity.get('indirectlyAffectedCount');
                    if (!count) return;
                    addRow(indirectTable, activity, _this.indirectlyAffectedActivities[activity.id], count)
                })
            }
            else {
                this.activityGroups.comparatorAttr = 'directlyAffectedCount';
                this.activityGroups.sort();
                this.activityGroups.forEach(function(group){
                    var count = group.get('directlyAffectedCount');
                    if (!count) return;
                    addRow(directTable, group, _this.directlyAffectedGroups[group.id], count)
                })

                this.activityGroups.comparatorAttr = 'indirectlyAffectedCount';
                this.activityGroups.sort();
                this.activityGroups.forEach(function(group){
                    var count = group.get('indirectlyAffectedCount');
                    if (!count) return;
                    addRow(indirectTable, group, _this.indirectlyAffectedGroups[group.id], count)
                })
            }
        },

        // render Step 7
        renderStakeholders: function(category){
            var _this = this,
                table = this.el.querySelector('#stakeholder-table'),
                header = table.insertRow(-1),
                fTh = document.createElement('th'),
                th = document.createElement('th');
            fTh.innerHTML = category.get('name');
            th.innerHTML = gettext('total');
            header.appendChild(fTh);
            header.appendChild(th);

            var userColumns = [];
            this.users.forEach(function(user){
                userColumns.push(user.id);
                var name = user.get('alias') || user.get('name'),
                    th = document.createElement('th');
                th.innerHTML = name;
                header.appendChild(th);
            })

            var colorStep = 70 / this.maxStakeholderCount;

            function renderItem(count, cell, options){
                //var options = (renderInfo) ? { 'overlayText' : '<span style="font-size: 29px;" class="glyphicon glyphicon-info-sign"></span>' } : {};
                var item = _this.panelItem(count + ' x', options);
                item.style.backgroundImage = 'none';
                //item.style.width = (renderInfo) ? '100px' : '50px';
                item.style.width = '50px';
                cell.appendChild(item);
                var sat = 100 - colorStep * count,
                    hsl = 'hsla(90, 50%, ' + sat + '%, 1)';
                if (sat < 50) item.style.color = 'white';
                item.style.backgroundColor = hsl;
            }
            var stakeholders = this.stakeholders[category.id];

            stakeholders.forEach(function(stakeholder){
                var count = _this.stakeholderCount[stakeholder.id] || 0;
                if (count) count = count['total']['count'];
                stakeholder.set('totalCount', count);
            })
            stakeholders.comparatorAttr = 'totalCount';
            stakeholders.sort();
            stakeholders.models.reverse();

            stakeholders.forEach(function(stakeholder){
                var row = table.insertRow(-1),
                    text = stakeholder.get('name');
                var panelItem = _this.panelItem(text);
                panelItem.style.maxWidth = '500px';
                row.insertCell(0).appendChild(panelItem);

                var valid = _this.stakeholderCount[stakeholder.id] != null;
                if (valid) {
                    var countItem = _this.stakeholderCount[stakeholder.id]['total'],
                        total = countItem['count'],
                        totalCell = row.insertCell(-1);
                    if (total) renderItem(total, totalCell, {
                        popoverText: '<b>' + stakeholder.get('name') + ' ' + gettext('assigned to') + '</b><br>' + countItem['solutions'].join('')
                    });
                }
                _this.users.forEach(function(user){
                    var cell = row.insertCell(-1);
                    if (!valid) return;
                    var count = _this.stakeholderCount[stakeholder.id][user.id];
                    if (count) renderItem(count['count'], cell, {
                        popoverText: '<b>' + stakeholder.get('name') + ' ' + gettext('assigned to') + '</b><br>' + count['solutions'].join('')
                    });
                })
            })
        },

    });
    return EvalStrategiesView;
}
);

