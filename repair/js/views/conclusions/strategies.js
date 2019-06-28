
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
                apiIds: [this.caseStudy.id, this.keyflowId]
            });
            this.strategies = options.strategies;
            this.stakeholderCategories = new GDSECollection([], {
                apiTag: 'stakeholderCategories',
                apiIds: [this.caseStudy.id]
            });
            promises = [];

            promises.push(this.stakeholderCategories.fetch({ error: this.onError }));
            promises.push(this.solutions.fetch({ error: this.onError }));
            promises.push(this.stakeholderCategories.fetch({ error: this.onError }))
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
                        },
                        error: _this.onError
                    }));
                })
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
            // step 7
            this.stakeholderCategories.forEach(function(category){
                _this.renderStakeholders(category);
            })
        },

        setupUsers: function(){
            var colorRange = chroma.scale(['red', 'yellow', 'blue', 'violet']),
                colorDomain = colorRange.domain([0, this.users.size()]),
                _this = this;
            this.userColors = {};
            this.stakeholderCount = {};
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

                implementations.forEach(function(implementation){
                    implementation.get('participants').forEach(function(stakeholderId){
                        if (!_this.stakeholderCount[stakeholderId])
                            _this.stakeholderCount[stakeholderId] = {};
                        if (!_this.stakeholderCount[stakeholderId][user.id])
                            _this.stakeholderCount[stakeholderId][user.id] = 0;
                        _this.stakeholderCount[stakeholderId][user.id] += 1;
                    })
                })
            })
            // sum up stakeholder counts
            this.maxStakeholderCount = 0;
            for (var stakeholderId in this.stakeholderCount) {
                var total = 0;
                Object.values(this.stakeholderCount[stakeholderId]).forEach(function(count){
                    total += count;
                })
                this.stakeholderCount[stakeholderId]['total'] = total;
                this.maxStakeholderCount = Math.max(this.maxStakeholderCount, total);
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
                header.appendChild(th.cloneNode(true));
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
                var implCount = 0;
                _this.users.forEach(function(user){
                    // insert empty cells so that the lines are drawn
                    row.insertCell(-1)
                    var strategies = _this.strategies.where({user: user.id});
                    if(strategies.length == 0) return;
                    var implementations = _this.implementations[strategies[0].id].where({ solution: solution.id });
                    implCount += implementations.length;
                });
                console.log(implCount)
                solItem.querySelector('.overlay').innerHTML = implCount + 'x';
                questions.forEach(function(question){
                    var qrow = table.insertRow(-1),
                        panelItem = _this.panelItem(question.get('question'));
                    panelItem.style.maxWidth = '400px';
                    panelItem.style.marginLeft = '200px';
                    var cell = qrow.insertCell(0);
                    cell.style.border = '0px';
                    cell.appendChild(panelItem);
                    _this.users.forEach(function(user){
                        var strategies = _this.strategies.where({user: user.id});
                        if(strategies.length == 0) return;
                        var strategy = strategies[0],
                            implementations = _this.implementations[strategy.id],
                            implementations = implementations.where({ solution: solution.id })
                        if (implementations.length == 0) return;
                        var implementation = implementations[0],
                            quantities = implementation.get('quantities');
                        // ToDo: multiple implementations?
                        console.log(quantities)
                    });
                });
            })

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
                header.appendChild(th.cloneNode(true));
            })

            var colorStep = 70 / this.maxStakeholderCount;

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

            this.stakeholders[category.id].forEach(function(stakeholder){
                var row = table.insertRow(-1),
                    text = stakeholder.get('name');
                var panelItem = _this.panelItem(text);
                panelItem.style.maxWidth = '500px';
                row.insertCell(0).appendChild(panelItem);

                var valid = _this.stakeholderCount[stakeholder.id] != null;
                if (valid) {
                    var countItem = _this.stakeholderCount[stakeholder.id],
                        total = countItem['total'],
                        totalCell = row.insertCell(-1);
                    if (total) renderItem(total, totalCell);
                }
                _this.users.forEach(function(user){
                    var cell = row.insertCell(-1);
                    if (!valid) return;
                    var count = _this.stakeholderCount[stakeholder.id][user.id];
                    if (count) renderItem(count, cell);
                })

            })

        },

    });
    return EvalStrategiesView;
}
);

