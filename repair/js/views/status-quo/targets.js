define(['underscore','views/baseview','models/aim', 'collections/aims',
 'collections/targetvalues', 'collections/targetspatialreference',
'collections/impactcategories', 'models/target', 'collections/targets'],

function(_, BaseView, Aim, Aims, TargetValues, TargetSpatialReference,
ImpactCategories, Target, Targets){
    /**
    *
    * @author Christoph Franke, Balázs Dukai
    * @name module:views/TargetsView
    * @augments Backbone.View
    */
    var TargetsView = BaseView.extend(
        /** @lends module:views/TargetsView.prototype */
        {

        /**
        * render setup view on targets
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
            var _this = this;
            _.bindAll(this, 'render');

            this.template = options.template;
            this.caseStudy = options.caseStudy;
            this.mode = options.mode || 0;

            _this.targets = [];
            this.targetsModel = new Targets([], {
                caseStudyId: _this.caseStudy.id
            });

            _this.aims = [];
            this.aimsModel = new Aims([], {
                caseStudyId: _this.caseStudy.id
            });

            // there is a spelling or conceptual error here, because
            // impactcategories == indicators
            _this.impactcategories = []
            this.impactCategoriesModel = new ImpactCategories([], {
            });

            _this.targetvalues = [];
            this.targetValuesModel = new TargetValues([], {
            });

            _this.spatial = [];
            this.spatialModel = new TargetSpatialReference([], {
            });

            this.targetsModel.fetch({
                success: function(targets){
                    var temp = [];
                    targets.forEach(function(target){
                        temp.push({
                            "id": target.get('id'),
                            "aim": target.get('aim'),
                            "impact_category": target.get('impact_category'),
                            "target_value": target.get('target_value'),
                            "spatial_reference": target.get('spatial_reference'),
                            "user": target.get('user')
                        });
                    });
                    _this.targets = _.sortBy(temp, 'aim' );
                    _this.render();
                },
                error: function(){
                    console.error("cannot fetch targets");
                }
            });

            this.aimsModel.fetch({
                success: function(aims){
                    _this.initItems(aims, _this.aims, "Aim");
                    _this.render();
                },
                error: function(){
                    console.error("cannot fetch aims");
                }
            });

            this.impactCategoriesModel.fetch({
                success: function(impactcategories){
                    impactcategories.forEach(function(impact){
                        _this.impactcategories.push({
                            "id": impact.get('id'),
                            "name": impact.get('name'),
                            "area_of_protection": impact.get('area_of_protection'),
                            "spatial_differentiation": impact.get('spatial_differentiation')
                        });
                    });
                    _this.render();
                },
                error: function(){
                    console.error("cannot fetch impactcategories");
                }
            });

            this.targetValuesModel.fetch({
                success: function(targets){
                    targets.forEach(function(target){
                        _this.targetvalues.push({
                            "text": target.get('text'),
                            "id": target.get('id'),
                            "number": target.get('number'),
                            "factor": target.get('factor')
                        });
                    });
                    _this.render();
                },
                error: function(){
                    console.error("cannot fetch targetvalues");
                }
            });

            this.spatialModel.fetch({
                success: function(areas){
                    areas.forEach(function(area){
                        _this.spatial.push({
                            "text": area.get('text'),
                            "name": area.get('name'),
                            "id": area.get('id')
                        });
                    });
                    _this.render();
                },
                error: function(){
                    console.error("cannot fetch targetspatialreference");
                }
            });

            this.render();
        },

        /*
        * dom events (managed by jquery)
        */
        events: {
            'click #add-target-button': 'addTarget'
        },

        initItems: function(items, list, type){
            items.forEach(function(item){
                list.push({
                    "text": item.get('text'),
                    "id": item.get('id'),
                    "type": type
                });
            });
        },

        /*
        * render the view
        */
        render: function(){
            var _this = this;
            var html = document.getElementById(this.template).innerHTML
            var template = _.template(html);
            this.el.innerHTML = template();
            this.renderRows();
        },

        renderRows(){
            var _this = this;
            for (var i = 0; i < this.targets.length; i++){
                var target = this.targets[i];
                var aim = _this.getObject(_this.aims, target.aim),
                    impactcategory = _this.getObject(_this.impactcategories,
                        target.impact_category),
                    targetValue = _this.getObject(_this.targetvalues,
                        target.target_value),
                    spatial = _this.getObject(_this.spatial,
                        target.spatial_reference);
                if (i == 0 || this.targets[i-1].aim != target.aim) {
                    var row = document.createElement('div');
                    row.classList.add('row', 'overflow', 'bordered');
                    var html = document.getElementById('target-row-template').innerHTML
                    var template = _.template(html);
                    row.innerHTML = template({ aim: aim.text, aimId: aim.id });
                    _this.el.appendChild(row);

                    var indicatorPanel = row.querySelector('.indicators').querySelector('.item-panel'),
                        targetPanel = row.querySelector('.targets').querySelector('.item-panel'),
                        spatialPanel = row.querySelector('.spatial').querySelector('.item-panel'),
                        html = document.getElementById('panel-item-template').innerHTML
                        template = _.template(html);
                }

                var panelItem = document.createElement('select');
                panelItem.classList.add('panel-item', 'form-control');
                _this.impactcategories.forEach(function(impactcategory){
                    var option = document.createElement('option');
                    option.text = impactcategory.name;
                    panelItem.appendChild(option);
                });
                for(var k, j = 0; k = panelItem.options[j]; j++) {
                    if(k.text == impactcategory.name) {
                        panelItem.selectedIndex = j;
                        break;
                    }
                }
                indicatorPanel.appendChild(panelItem);

                var targetSelect = document.createElement('select');
                targetSelect.classList.add('panel-item', 'form-control');
                _this.targetvalues.forEach(function(target){
                    var option = document.createElement('option');
                    option.text = target.text;
                    targetSelect.appendChild(option);
                });
                for(var k, j = 0; k = targetSelect.options[j]; j++) {
                    if(k.text == targetValue.text) {
                        targetSelect.selectedIndex = j;
                        break;
                    }
                }
                targetPanel.appendChild(targetSelect);

                var spatialSelect = document.createElement('select');
                spatialSelect.classList.add('panel-item', 'form-control');
                _this.spatial.forEach(function(s){
                    var option = document.createElement('option');
                    option.text = s.text;
                    spatialSelect.appendChild(option);
                });
                for(var k, j = 0; k = spatialSelect.options[j]; j++) {
                    if(k.text == spatial.text) {
                        spatialSelect.selectedIndex = j;
                        break;
                    }
                }
                spatialPanel.appendChild(spatialSelect);
            }
        },

        getObject(list, id){
            var pos = list.map(function(e) {
                return e.id;
            }).indexOf(id);
            return list[pos];
        },

        addTarget: function(e){
            var _this = this;
            var aimId = $(e.currentTarget).attr("aimId");
            // just create a default Target
            var target = new Target(
                {
                "aim": aimId,
                "impact_category": _this.impactcategories[0].id,
                "target_value": _this.targetvalues[0].id,
                "spatial_reference": _this.spatial[0].id
                },
                { caseStudyId: _this.caseStudy.id}
            );
            target.save(null, {
                success: function(){
                    var temp = _this.targets;
                    temp.push({
                        "id": target.get('id'),
                        "aim": target.get('aim'),
                        "impact_category": target.get('impact_category'),
                        "target_value": target.get('target_value'),
                        "spatial_reference": target.get('spatial_reference'),
                        "user": target.get('user')
                    });
                    _this.targets = _.sortBy(temp, 'aim' );
                    _this.render();
                },
                error: function(){
                    console.error("cannot addTarget");
                }
            });
        },

        /*
        * remove this view from the DOM
        */
        close: function(){
            this.undelegateEvents(); // remove click events
            this.unbind(); // Unbind all local event bindings
            this.el.innerHTML = ''; //empty the DOM element
        },

    });
    return TargetsView;
}
);
