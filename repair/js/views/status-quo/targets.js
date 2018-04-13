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

        createSelect(type, typeObject, typeList, target){
            var _this = this;
            var select = document.createElement('select');
            // var type = "targetvalue";
            var selectId = type + typeObject.id;
            select.classList.add('panel-item', 'form-control');
            typeList.forEach(function(target){
                var option = document.createElement('option');
                if (type == "impact") {
                    option.text = target.name;
                } else {
                    option.text = target.text;
                }
                option.setAttribute("id", target.id);
                select.appendChild(option);
            });
            for(var k, j = 0; k = select.options[j]; j++) {
                if (type == "impact") {
                    if(k.text == typeObject.name) {
                        select.selectedIndex = j;
                        break;
                    }
                } else {
                    if(k.text == typeObject.text) {
                        select.selectedIndex = j;
                        break;
                    }
                }
            }
            select.setAttribute("type", type);
            select.setAttribute("id", selectId);
            select.setAttribute("targetId", target.id);
            select.addEventListener("change", function(e){
                _this.editTarget(e, target);
            });
            return select;
        },

        renderRows(){
            var _this = this;
            for (var i = 0; i < this.targets.length; i++){
                var target = this.targets[i];
                var aim = _this.getObject(_this.aims, target.aim),
                    impactCategory = _this.getObject(_this.impactcategories,
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

                var targetSelect = _this.createSelect("targetvalue", targetValue,
                 _this.targetvalues, target);
                targetPanel.appendChild(targetSelect);

                var panelItem = _this.createSelect("impact", impactCategory,
                _this.impactcategories, target);
                indicatorPanel.appendChild(panelItem);

                var spatialSelect = _this.createSelect("spatial", spatial,
                _this.spatial, target);
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

        editTarget: function(e){
            var _this = this;
            var select = $(e)[0].target;
            var type = select.getAttribute("type");
            var targetId = parseInt(select.getAttribute("targetId"));
            var idx = select.options.selectedIndex;
            var optionId = parseInt(select.options[idx].getAttribute("id"));
            var target = new Target(
                {id: targetId},
                {caseStudyId: _this.caseStudy.id}
            );
            // console.log(target);
            if (type == "targetvalue") {
                target.save({
                    target_value: optionId
                }, {
                    patch: true,
                    error: function(){
                        console.error("cannot update targetvalue");
                    }
                });
            } else if (type == "impact") {
                console.log("save impact");
                target.save({
                    "impact_category": optionId
                }, {
                    patch: true,
                    error: function(){
                        console.error("cannot update impact");
                    }
                });
            } else {
                console.log("save spatial");
                target.save({
                    "spatial_reference": optionId
                }, {
                    patch: true,
                    error: function(){
                        console.error("cannot update spatial");
                    }
                });
            }
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
