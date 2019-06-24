
define(['underscore','views/common/baseview', 'collections/gdsecollection'],

function(_, BaseView, GDSECollection, Muuri){
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

            this.loader.activate();
            promises = [];

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
                                _this.indicatorValues[indicator.id][user.id] = data;
                            },
                            error: _this.onError
                        })
                    )
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
            this.renderIndicators()
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
                var panelItem = _this.panelItem(text)
                panelItem.style.maxWidth = '500px';
                row.insertCell(0).appendChild(panelItem);
                userColumns.forEach(function(userId){
                    var cell = row.insertCell(-1),
                        data = _this.indicatorValues[indicator.id][userId];
                    if (!data) return;
                    var data = data[0],
                        strategyValue = data.value;
                        deltaValue = data.delta || 0,
                        isAbs = indicator.get('is_absolute'),
                        statusquoValue = strategyValue - deltaValue;
                    if (!statusquoValue) return;
                    var deltaPerc = (isAbs) ? deltaValue / statusquoValue * 100 : deltaValue,
                        unit = indicator.get('unit'),
                        dt = (deltaPerc > 0) ? '+' + _this.format(deltaPerc) : _this.format(deltaPerc);
                        item = _this.panelItem(dt + '%');
                    cell.appendChild(item);
                    var hue = (deltaPerc >= 0) ? 90 : 0, // green or red
                        sat = 100 - 70 * Math.abs(Math.min(deltaPerc / 100, 1)),
                        hsl = 'hsla(' + hue + ', 50%, ' + sat + '%, 1)';
                    if (sat < 50) item.style.color = 'white';
                    item.style.backgroundImage = 'none';
                    item.style.backgroundColor = hsl;
                })

            })

        },
    });
    return EvalModifiedFlowsView;
}
);

