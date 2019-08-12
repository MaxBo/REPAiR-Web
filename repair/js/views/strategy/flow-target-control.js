define(['views/common/baseview', 'collections/gdsecollection',
        'views/status-quo/workshop-flow-assessment', 'models/indicator',
        'visualizations/barchart',
        'utils/utils', 'underscore', 'static/css/status-quo.css'],

function(BaseView, GDSECollection, FlowAssessmentWorkshopView, Indicator, BarChart,
         utils, _){
/**
*
* @author Christoph Franke
* @name module:views/FlowTargetControlView
* @augments module:views/BaseView
*/
var FlowTargetControlView = BaseView.extend(
    /** @lends module:views/FlowTargetControlView.prototype */
    {

    /**
    * view to render indicators in strategy
    *
    * @param {Object} options
    */
    initialize: function(options){
        var _this = this;
        FlowTargetControlView.__super__.initialize.apply(this, [options]);
        this.caseStudy = options.caseStudy;
        this.keyflowId = options.keyflowId;
        this.strategy = options.strategy;

        //this.aims = options.aims;

        var promises = [];
        this.userObjectives = new GDSECollection([], {
            apiTag: 'userObjectives',
            apiIds: [this.caseStudy.id],
            comparator: 'priority'
        });

        this.aims = new GDSECollection([], {
            apiTag: 'aims',
            apiIds: [this.caseStudy.id],
            comparator: 'priority'
        });

        this.indicators = new GDSECollection([], {
            apiTag: 'flowIndicators',
            apiIds: [this.caseStudy.id, this.keyflowId],
            comparator: 'name',
            model: Indicator
        });

        this.targetValues = new GDSECollection([], {
            apiTag: 'targetvalues',
        });

        promises.push(this.userObjectives.fetch({
            data: { keyflow: this.keyflowId },
            error: this.onError
        }));

        promises.push(this.aims.fetch({
            data: { keyflow: this.keyflowId },
            error: this.onError
        }));

        promises.push(this.indicators.fetch({error: this.onError}))
        promises.push(this.targetValues.fetch({error: this.onError}))

        this.targets = {};
        this.loader.activate();
        Promise.all(promises).then(function(){
            var promises = [];
            _this.userObjectives.forEach(function(objective){
                var targets = new GDSECollection([], {
                    apiTag: 'flowTargets',
                    apiIds: [_this.caseStudy.id, objective.id]
                })
                _this.targets[objective.id] = targets;
                promises.push(targets.fetch({error: _this.onError}));
            });
            Promise.all(promises).then(function(){
                _this.loader.deactivate();
                _this.render();
            });
        });

    },

    /*
    * dom events (managed by jquery)
    */
    events: {
    },

    render: function(){
        var html = document.getElementById(this.template).innerHTML,
            template = _.template(html),
            _this = this;
        this.el.innerHTML = template();
        this.assessmentView = new FlowAssessmentWorkshopView({
            caseStudy: this.caseStudy,
            el: this.el.querySelector('#modified-indicators'),
            template: 'workshop-flow-assessment-template',
            keyflowId: this.keyflowId,
            strategy: this.strategy
        })
        var objectivesPanel = this.el.querySelector('#target-control');
        this.userObjectives.forEach(function(objective){
            var panel = _this.renderObjective(objective);
            objectivesPanel.appendChild(panel);
        });
    },

    renderObjective: function(objective){
        var _this = this,
            objectivePanel = document.createElement('div'),
            html = document.getElementById('objective-control-template').innerHTML,
            template = _.template(html),
            aim = this.aims.get(objective.get('aim')),
            targets = this.targets[objective.id];

        objectivePanel.innerHTML = template({
            id: objective.id,
            title: aim.get('text'),
            year: _this.caseStudy.get('properties')['target_year']
        });
        var targetEl = objectivePanel.querySelector('div[name="indicator-rows"]');

        targets.forEach(function(target){
            var indicatorRow = _this.renderIndicatorRow(target, objective);
            targetEl.appendChild(indicatorRow);
        })

        return objectivePanel;
    },

    renderIndicatorRow: function(target, objective){
        var _this = this,
            row = document.createElement('div'),
            html = document.getElementById('indicator-control-template').innerHTML,
            template = _.template(html);

        row.classList.add('row','bordered');
        row.style.minHeight = "200px";

        function setSpatialRef(indicatorId){
            var spatialRef = _this.indicators.get(indicatorId).get('spatial_reference'),
                label = (spatialRef === 'REGION') ? gettext('Casestudy Region') : gettext('Focus Area');
            spatialInput.value = label;
        }
        var indicator = this.indicators.get(target.get('indicator')),
            spatialRef = indicator.get('spatial_reference'),
            targetValue = this.targetValues.get(target.get('target_value'));

        var spatial_label = (spatialRef === 'REGION') ? gettext('casestudy region') : gettext('focus area'),
            title = indicator.get('name') + ' (in the ' + spatial_label + ')';

        loader = new utils.Loader(row);
        loader.activate();

        function render(data){
            loader.deactivate();
            var data = data[0],
                strategyValue = data.value || 0,
                deltaValue = data.delta || 0,
                isAbs = indicator.get('is_absolute'),
                statusquoValue = strategyValue - deltaValue,
                deltaPerc = (isAbs) ? deltaValue / statusquoValue * 100 : deltaValue,
                unit = indicator.get('unit'),
                deltaText = _this.format(deltaValue) + ' ' + unit,
                status = 0;

            if (isAbs && statusquoValue != 0){
                var dt = (deltaPerc > 0) ? '+' + _this.format(deltaPerc) : _this.format(deltaPerc);
                deltaText += ' (' + dt + '%)'
            }

            var targetPerc = targetValue.get('number') * 100;

            // right direction but target not reached
            if ((targetPerc < 0 && deltaPerc < 0) || (targetPerc > 0 && deltaPerc > 0))
                status = 1;

            // target reached
            if ((targetPerc == deltaPerc) || (targetPerc < 0 && deltaPerc <= targetPerc) || (targetPerc > 0 && deltaPerc >= targetPerc))
                status = 2;

            row.innerHTML = template({
                title: title,
                status: status,
                statusquoValue: _this.format(statusquoValue) + ' ' + unit,
                strategyValue: _this.format(strategyValue) + ' ' + unit,
                deltaValue: deltaText,
                targetValue: targetValue.get('text')
            });

            deltaText = _this.format(deltaPerc) + '%';
            if (deltaPerc > 0) deltaText = '+' + deltaText;
            var targetText = _this.format(targetPerc) + '%';
            if (targetPerc > 0) targetText = '+' + targetText;
            var chartData = [
                { name: gettext('Strategy'), value: deltaPerc || 0, text: deltaText, color: '#4a8ef9'},
                { name: gettext('Target'), value: targetPerc, text: targetText, color: '#cecece'}
            ]

            var barChart = new BarChart({
                el: row.querySelector('div[name="chart"]'),
                width: 500,
                height: 200,
                min: -100,
                max: 100
            })
            barChart.draw(chartData);
        }

        var geom = (spatialRef == 'REGION') ? this.caseStudy.get('geometry') : this.caseStudy.get('properties').focusarea;

        indicator.compute({
            method: "POST",
            data: {
                geom: JSON.stringify(geom),
                strategy: _this.strategy.id
            },
            success: render,
            error: function(){
                loader.deactivate();
            }
        })

        return row;
    },

    close: function(){
        this.assessmentView.close();
        FlowTargetControlView.__super__.close.apply(this);
    }
});
return FlowTargetControlView;
}
);


