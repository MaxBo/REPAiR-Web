
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
            this.keyflowId = options.keyflowId;
            this.users = options.users;

            this.solutions = new GDSECollection([], {
                apiTag: 'solutions',
                apiIds: [this.caseStudy.id, this.keyflowId]
            });
            this.strategies = new GDSECollection([], {
                apiTag: 'strategies',
                apiIds: [this.caseStudy.id, this.keyflowId]
            });
            promises = [];
            promises.push(this.solutions.fetch({ error: this.onError }));
            promises.push(this.strategies.fetch({
                data: { 'user__in': this.users.pluck('id').join(',') },
                error: this.onError
            }));

            this.loader.activate();
            Promise.all(promises).then(function(){
                _this.loader.deactivate();
                _this.render();
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
                template = _.template(html);
            this.el.innerHTML = template({ solutions: this.solutions });
            this.solutionSelect = this.el.querySelector('select[name="solutions"]')
            this.elLegend = this.el.querySelector('.legend');
            this.setupUsers();
            this.setupStrategiesMap();
        },

        setupUsers: function(){
            var colorRange = chroma.scale(['red', 'yellow', 'blue', 'violet']),
                colorDomain = colorRange.domain([0, this.users.size()]),
                _this = this;
            this.userColors = {};
            var i = 0;
            this.users.forEach(function(user){
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
            })
        },

        setupStrategiesMap: function(){
            var _this = this;
            this.strategiesMap = new Map({
                el: this.el.querySelector('#strategies-map'),
                opacity: 0.5
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

        drawImplementations: function(){
            var solution = this.solutions.get(this.solutionSelect.value),
                possImplArea = solution.get('possible_implementation_area'),
                focusarea = this.caseStudy.get('properties').focusarea,
                _this = this;

            this.users.forEach(function(user){
                _this.strategiesMap.clearLayer('user' + user.id);
            })

            if (possImplArea) {
                var poly = new ol.geom.MultiPolygon(possImplArea.coordinates);
                this.strategiesMap.centerOnPolygon(poly, { projection: this.projection });
            } else if (focusarea){
                var poly = new ol.geom.MultiPolygon(focusarea.coordinates);
                this.strategiesMap.centerOnPolygon(poly, { projection: this.projection });
            };

            var userSolutions = {},
                promises = [];

            this.strategies.forEach(function(strategy){
                // strategy does not implement solution
                if(strategy.get('solutions').indexOf(solution.id) == -1) return;
                var sol = new GDSECollection([], {
                    apiTag: 'solutionsInStrategy',
                    apiIds: [_this.caseStudy.id, _this.keyflowId, strategy.id]
                });
                userSolutions[strategy.get('user')] = sol;
                promises.push(sol.fetch({
                    data: { solution: solution.id }
                }))
            })
            this.loader.activate();
            Promise.all(promises).then(function(){
                for (var userId in userSolutions){
                    var implementations = userSolutions[userId],
                        user = _this.users.get(userId),
                        userName = user.get('alias') || user.get('name');
                    implementations.forEach(function(solutionImpl){
                        var implAreas = solutionImpl.get('geom');
                        // implementation areas are collections
                        if (!implAreas || implAreas.geometries.length == 0) return;
                        implAreas.geometries.forEach(function(geom){
                            _this.strategiesMap.addGeometry(geom.coordinates, {
                                projection: 'EPSG:3857',
                                layername: 'user' + userId,
                                type: geom.type,
                                tooltip: userName
                            });
                        })
                    })
                }
                _this.loader.deactivate();
            })
        }
    });
    return EvalStrategiesView;
}
);

