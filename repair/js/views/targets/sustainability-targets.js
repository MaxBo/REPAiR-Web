define(['underscore','views/common/baseview', 'collections/gdsecollection',
        'models/gdsemodel'],

function(_, BaseView, GDSECollection, GDSEModel){
    /**
    *
    * @author Christoph Franke, Balázs Dukai
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
            this.mode = options.mode || 0;

            this.aims = new GDSECollection([], {
                apiTag: 'aims',
                apiIds: [this.caseStudy.id],
                comparator: 'priority'
            });
            this.targets = {};

            // there is a spelling or conceptual error here, because
            // impactcategories == indicators
            this.impactcategories = new GDSECollection([], {
                apiTag: 'impactcategories'
            });

            this.targetvalues = new GDSECollection([], {
                apiTag: 'targetvalues',
            });

            this.spatial = new GDSECollection([], {
                apiTag: 'targetspatialreference',
            });

            var promises = [];

            promises.push(this.impactcategories.fetch({
                error: _this.onError
            }));

            promises.push(this.targetvalues.fetch({
                error: _this.onError
            }));

            promises.push(this.spatial.fetch({
                error: _this.onError
            }));

            this.aims.fetch({
                data: {
                    keyflow: this.keyflowId
                },
                success: function(){
                    _this.aims.forEach(function(aim){
                        _this.targets[aim.id] = new GDSECollection([], {
                            apiTag: 'targets',
                            apiIds: [_this.caseStudy.id, aim.id]
                        });
                        promises.push(_this.targets[aim.id].fetch({error: _this.onError}));
                        Promise.all(promises).then(_this.render);
                    })
                },
                error: _this.onError
            });

        },

        /*
        * dom events (managed by jquery)
        */
        events: {
            'click .add-target': 'addTarget'
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

        createSelect(type, typeObject, typeList, target, aimId){
            var _this = this;
            var select = document.createElement('select'),
                wrapper = document.createElement('div');
            // var type = "targetvalue";
            wrapper.classList.add('fake-cell');
            select.classList.add('form-control');
            typeList.forEach(function(target){
                var option = document.createElement('option');
                if (type == "impact") {
                    option.text = target.get('name');
                } else {
                    option.text = target.get('text');
                }
                option.value = target.id;
                select.appendChild(option);
            });
            select.value = typeObject.id;

            select.setAttribute("type", type);
            select.setAttribute("aimId", aimId);
            select.setAttribute("targetId", target.id);
            select.addEventListener("change", function(e){
                _this.editTarget(e, target);
            });
            wrapper.appendChild(select);
            return wrapper;
        },

        renderRows(){
            var _this = this;
            _this.aims.forEach(function(aim){
                var row = document.createElement('div');
                row.classList.add('row', 'overflow', 'bordered');
                var html = document.getElementById('sustainability-target-row-template').innerHTML
                var template = _.template(html);
                row.innerHTML = template({ aim: aim.get('text'), aimId: aim.id });
                _this.el.appendChild(row);
                var indicatorPanel = row.querySelector('.indicators').querySelector('.item-panel'),
                    targetPanel = row.querySelector('.targets').querySelector('.item-panel'),
                    spatialPanel = row.querySelector('.spatial').querySelector('.item-panel'),
                    removePanel = row.querySelector('.remove').querySelector('.item-panel'),
                    html = document.getElementById('panel-item-template').innerHTML,
                    template = _.template(html);
                var targets = _this.targets[aim.id];
                targets.forEach(function(target){
                    var impactCategory = _this.impactcategories.get(target.get('impact_category')),
                        targetValue = _this.targetvalues.get(target.get('target_value')),
                        spatial = _this.spatial.get(target.get('spatial_reference'));
                    var removeBtn = document.createElement('button');
                    var targetSelect = _this.createSelect("targetvalue", targetValue,
                        _this.targetvalues, target, aim.id);
                    targetPanel.appendChild(targetSelect);

                    var panelItem = _this.createSelect("impact", impactCategory,
                        _this.impactcategories, target, aim.id);
                    indicatorPanel.appendChild(panelItem);

                    var spatialSelect = _this.createSelect("spatial", spatial,
                        _this.spatial, target, aim.id);
                    spatialPanel.appendChild(spatialSelect);

                    removeBtn.classList.add("btn", "btn-warning", "square", "remove");
                    // removeBtn.style.float = 'right';
                    var span = document.createElement('span');
                    removeBtn.title = gettext('Remove target')
                    span.classList.add('glyphicon', 'glyphicon-minus');
                    // make span unclickable (caused problems when trying to
                    // delete row, as the span has no id attached)
                    span.style.pointerEvents = 'none';
                    removeBtn.appendChild(span);
                    removeBtn.setAttribute("targetId", target.id);
                    removeBtn.setAttribute("aimId", aim.id);
                    removeBtn.addEventListener('click', function(e){
                        _this.deleteTarget(e);
                    })
                    var btnDiv = document.createElement('div');
                    btnDiv.classList.add("row", "fake-cell");
                    btnDiv.appendChild(removeBtn);
                    removePanel.appendChild(btnDiv);
                })
            })
        },

        addTarget: function(e){
            var _this = this;
            var aimId = $(e.currentTarget).attr("aimId");
            // just create a default Target
            var target = this.targets[aimId].create(
                {
                    "aim": aimId,
                    "impact_category": _this.impactcategories.first().id,
                    "target_value": _this.targetvalues.first().id,
                    "spatial_reference": _this.spatial.first().id
                },
                {
                    wait: true,
                    success: function(){
                        _this.render();
                    },
                    error: _this.onError
                }
            );
        },

        editTarget: function(e){
            var _this = this;
            var select = $(e)[0].target;
            var type = select.getAttribute("type");
            var targetId = parseInt(select.getAttribute("targetId"));
            var aimId = parseInt(select.getAttribute("aimId"));
            var optionId = parseInt(select.value);
            var target = _this.targets[aimId].get(targetId);
            if (type == "targetvalue") {
                target.save({
                    target_value: optionId
                }, {
                    patch: true,
                    error: _this.onError
                });
            } else if (type == "impact") {
                target.save({
                    "impact_category": optionId
                }, {
                    patch: true,
                    error: _this.onError
                });
            } else {
                target.save({
                    "spatial_reference": optionId
                }, {
                    patch: true,
                    error: _this.onError
                });
            }
        },

        deleteTarget: function(e){
            var _this = this;
            var button = $(e)[0].target;
            var targetId = parseInt(button.getAttribute("targetId"));
            var aimId = parseInt(button.getAttribute("aimId"));
            var message = gettext('Do you really want to delete the target?');
            _this.confirm({ message: message, onConfirm: function(){
                var target = _this.targets[aimId].get(targetId);
                target.destroy({
                    success: function(){
                        _this.render();
                    },
                    error: _this.onError
                });
            }});
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
    return SustainabilityTargetsView;
}
);
