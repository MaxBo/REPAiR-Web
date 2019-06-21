define(['views/common/baseview', 'underscore', 'collections/gdsecollection',
        'collections/geolocations', 'visualizations/map', 'viewerjs', 'app-config',
        'utils/utils', 'bootstrap', 'viewerjs/dist/viewer.css'],

function(BaseView, _, GDSECollection, GeoLocations, Map, Viewer, config,
         utils){
/**
*
* @author Christoph Franke
* @name module:views/SolutionsWorkshopView
* @augments BaseView
*/
var SolutionsWorkshopView = BaseView.extend(
    /** @lends module:views/SolutionsWorkshopView.prototype */
    {

    /**
    * render setup and workshop view on solutions
    *
    * @param {Object} options
    * @param {HTMLElement} options.el                          element the view will be rendered in
    * @param {string} options.template                         id of the script element containing the underscore template to render this view
    * @param {module:models/CaseStudy} options.caseStudy       the casestudy to add solutions to
    *
    * @constructs
    * @see http://backbonejs.org/#View
    */
    initialize: function(options){
        SolutionsWorkshopView.__super__.initialize.apply(this, [options]);
        var _this = this;
        _.bindAll(this, 'renderCategory');

        this.template = options.template;
        this.caseStudy = options.caseStudy;
        this.keyflowId = options.keyflowId;
        this.keyflowName = options.keyflowName;

        this.categories = new GDSECollection([], {
            apiTag: 'solutionCategories',
            apiIds: [this.caseStudy.id, this.keyflowId]
        });

        this.solutions = new GDSECollection([], {
            apiTag: 'solutions',
            apiIds: [this.caseStudy.id, this.keyflowId]
        });

        this.activities = new GDSECollection([], {
            apiTag: 'activities',
            apiIds: [this.caseStudy.id, this.keyflowId]
        });
        var promises = [];
        promises.push(this.categories.fetch(), this.solutions.fetch());

        this.loader.activate();
        Promise.all(promises).then(function(){
            _this.loader.deactivate();
            _this.render();
        });
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
    },

    /*
    * render the view
    */
    render: function(){
        var _this = this;
        var html = document.getElementById(this.template).innerHTML
        var template = _.template(html);
        this.el.innerHTML = template({
            keyflowName: this.keyflowName
        });
        var promises = [];
        this.categories.forEach(function(category){
            var solutions = _this.solutions.filterBy({solution_category: category.id})
            _this.renderCategory(category, solutions);
        });
    },

    /*
    * open a modal containing details about the solution
    * onConfirm is called when user confirms modal by clicking OK button
    */
    showSolution: function(solution, onConfirm){
        var _this = this,
            changedImages = {};

        var category = this.categories.get(solution.get('solution_category'));
        var html = document.getElementById('view-solution-template').innerHTML,
            template = _.template(html),
            modal = this.el.querySelector('#solution-modal');

        modal.innerHTML = template({
            name: solution.get('name'),
            description: solution.get('description'),
            notes: solution.get('documentation'),
            effectSrc: solution.get('effect_image'),
            stateSrc: solution.get('currentstate_image'),
            activitiesSrc: solution.get('activities_image'),
            category: category.get('name')
        });
        //this.renderMatFilter();
        var okBtn = modal.querySelector('.confirm');
        if (this.viewer) this.viewer.destroy();
        this.viewer = new Viewer.default(modal);

        $(modal).modal('show');
    },

    /*
    * render a solution category panel
    * adds buttons in setup mode only
    */
    renderCategory: function(category, solutions){
        var _this = this;
        var panelList = this.el.querySelector('#categories');
        // create the panel (ToDo: use template for panels instead?)
        var div = document.createElement('div'),
            panel = document.createElement('div');
        div.classList.add('item-panel', 'bordered');
        div.style.minWidth = '300px';
        var label = document.createElement('label');
        label.innerHTML = category.get('name');
        label.style.marginBottom = '20px';

        panelList.appendChild(div);
        div.appendChild(label);
        div.appendChild(panel);
        // add the items
        solutions.forEach(function(solution){
            _this.renderSolutionItem(panel, solution);
        });
    },

    /*
    * render a solution item in the panel
    */
    renderSolutionItem: function(panel, solution){
        var _this = this;
        // render panel item from template (in templates/common.html)
        //var html = document.getElementById('panel-item-template').innerHTML,
            //template = _.template(html);
        var panelItem = _this.panelItem(solution.get('name'), {
            overlayText: '<span style="font-size: 29px;" class="glyphicon glyphicon-info-sign"></span>'
        })
        panel.appendChild(panelItem);
        panelItem.addEventListener('click', function(){
            _this.showSolution(solution);
        })
    }

});
return SolutionsWorkshopView;
}
);
