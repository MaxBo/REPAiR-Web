define(['views/common/baseview', 'views/common/flows',
        'collections/gdsecollection', 'underscore'],

function(BaseView, FlowsView, GDSECollection, _){
/**
*
* @author Christoph Franke
* @name module:views/ModifiedFlowsView
* @augments module:views/BaseView
*/
var ModifiedFlowsView = BaseView.extend(
    /** @lends module:views/ModifiedFlowsView.prototype */
    {

    /**
    * render view to show keyflows in strategy
    *
    * @param {Object} options
    * @param {HTMLElement} options.el                     element the view will be rendered in
    * @param {string} options.template                    id of the script element containing the underscore template to render this view
    * @param {module:models/CaseStudy} options.caseStudy  the casestudy to add layers to
    *
    * @constructs
    * @see http://backbonejs.org/#View
    */
    initialize: function(options){
        var _this = this;
        ModifiedFlowsView.__super__.initialize.apply(this, [options]);
        this.caseStudy = options.caseStudy;
        this.keyflowId = options.keyflowId;
        this.strategy = options.strategy;
        this.filters = new GDSECollection([], {
            apiTag: 'flowFilters',
            apiIds: [this.caseStudy.id, this.keyflowId],
            comparator: 'name'
        })
        this.caseStudy = options.caseStudy;
        this.keyflowId = options.keyflowId;
        this.materials = new GDSECollection([], {
            apiTag: 'materials',
            apiIds: [this.caseStudy.id, this.keyflowId ]
        });
        this.activities = new GDSECollection([], {
            apiTag: 'activities',
            apiIds: [this.caseStudy.id, this.keyflowId ],
            comparator: 'name'
        });
        this.activityGroups = new GDSECollection([], {
            apiTag: 'activitygroups',
            apiIds: [this.caseStudy.id, this.keyflowId ],
            comparator: 'name'
        });
        this.actors = new GDSECollection([], {
            apiTag: 'actors',
            apiIds: [this.caseStudy.id, this.keyflowId],
            comparator: 'name'
        })
        var promises = [
            this.activities.fetch(),
            this.activityGroups.fetch(),
            this.materials.fetch(),
            this.filters.fetch({ data: { included: "True" } })
        ]
        this.loader.activate();
        Promise.all(promises).then(function(){
            _this.loader.deactivate();
            _this.render();
        })
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'change select[name="filter"]': 'changeFilter',
        'change select[name="display-level-select"]': 'draw'
    },

    /*
    * render the view
    */
    render: function(){
        var _this = this,
            html = document.getElementById(this.template).innerHTML,
            template = _.template(html);
        this.el.innerHTML = template({ filters: this.filters });
        this.flowFilterSelect = this.el.querySelector('select[name="filter"]');
        this.descriptionLabel = this.el.querySelector('#filter-description');
        this.displayLevelSelect = this.el.querySelector('select[name="display-level-select"]');
        this.flowsEl = this.el.querySelector('#flows-render-content');
        this.displayLevelSelect.disabled = true;
        this.flowsEl.style.visibility = 'hidden';
        var popovers = this.el.querySelectorAll('[data-toggle="popover"]');
        $(popovers).popover({ trigger: "focus" });
    },

    renderFlowsView: function(){
    },

    // fetch and show selected indicator
    changeFilter: function(){
        var selected = this.flowFilterSelect.value,
            filter = this.filters.get(selected);
        this.displayLevelSelect.disabled = false;
        this.flowsEl.style.visibility = 'visible';
        this.descriptionLabel.innerHTML = filter.get('description');
        if (this.flowsView) this.flowsView.close();
        this.flowsView = new FlowsView({
            el: this.flowsEl,
            template: 'flows-render-template',
            materials: this.materials,
            actors: this.actors,
            activityGroups: this.activityGroups,
            activities: this.activities,
            caseStudy: this.caseStudy,
            keyflowId: this.keyflowId,
            filter: filter,
            strategy: this.strategy
        });
        this.draw();
    },

    draw: function(){
        var displayLevel = this.displayLevelSelect.value;
        if (this.flowsView) this.flowsView.draw(displayLevel);
    },

    close: function(){
        if (this.flowsView) this.flowsView.close();
        ModifiedFlowsView.__super__.close.call(this);
    }

});
return ModifiedFlowsView;
}
);


