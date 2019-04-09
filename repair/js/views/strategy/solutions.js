define(['views/common/baseview', 'underscore', 'collections/gdsecollection',
        'collections/geolocations', 'visualizations/map', 'viewerjs', 'app-config',
        'utils/utils', 'summernote', 'summernote/dist/summernote.css',
        'bootstrap', 'viewerjs/dist/viewer.css'],

function(BaseView, _, GDSECollection, GeoLocations, Map, Viewer, config,
         utils, summernote){
/**
*
* @author Christoph Franke
* @name module:views/SolutionsView
* @augments BaseView
*/
var SolutionsView = BaseView.extend(
    /** @lends module:views/SolutionsView.prototype */
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
        SolutionsView.__super__.initialize.apply(this, [options]);
        var _this = this;
        _.bindAll(this, 'renderCategory');

        this.template = options.template;
        this.caseStudy = options.caseStudy;
        this.keyflowId = options.keyflowId;
        this.keyflowName = options.keyflowName;
        this.mode = options.mode || 0;

        // ToDo: replace with collections fetched from server
        this.categories = new GDSECollection([], {
            apiTag: 'solutionCategories',
            apiIds: [this.caseStudy.id, this.keyflowId]
        }),

        this.activities = new GDSECollection([], {
            apiTag: 'activities',
            apiIds: [this.caseStudy.id, this.keyflowId]
        });
        var promises = [];
        promises.push(this.categories.fetch());
        promises.push(this.activities.fetch());

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
        'click .chart-control.fullscreen-toggle ': 'toggleFullscreen',
        'click #add-solution-category': 'addCategory'
    },

    /*
    * render the view
    */
    render: function(){
        var _this = this;
        var html = document.getElementById(this.template).innerHTML
        var template = _.template(html);
        this.el.innerHTML = template({
            mode: this.mode,
            keyflowName: this.keyflowName
        });
        var promises = [];
        this.loader.activate();
        this.categories.forEach(function(category){
            category.solutions = new GDSECollection([], {
                apiTag: 'solutions',
                apiIds: [_this.caseStudy.id, _this.keyflowId, category.id]
            }),
            promises.push(category.solutions.fetch());
        });
        // fetch all before rendering to keep the order
        Promise.all(promises).then(function(){
            _this.categories.forEach(function(category){
                _this.renderCategory(category);
            });
            _this.loader.deactivate();

            // lazy way to render workshop mode: just hide all buttons for editing
            // you may make separate views as well
            if (_this.mode == 0){
                var btns = _this.el.querySelectorAll('button.add, button.edit, button.remove');
                _.each(btns, function(button){
                    button.style.display = 'none';
                });
            }
        });
    },



    /*
    * open a modal containing details about the solution
    * onConfirm is called when user confirms modal by clicking OK button
    */
    showSolution: function(solution, onConfirm){
        var _this = this,
            changedImages = {};

        function swapImage(input, imgId, field){
            if (input.files && input.files[0]){
                var reader = new FileReader();
                reader.onload = function (e) {
                    document.getElementById(imgId).src = e.target.result;
                };
                reader.readAsDataURL(input.files[0]);
                changedImages[field] = input.files[0];
            }
        };

        var category = this.categories.get(solution.get('solution_category'));
        var html = document.getElementById('view-solution-template').innerHTML,
            template = _.template(html),
            modal = this.el.querySelector('#solution-modal');

        modal.innerHTML = template({
            name: solution.get('name'),
            description: solution.get('description'),
            effectSrc: solution.get('effect_image'),
            stateSrc: solution.get('currentstate_image'),
            activitiesSrc: solution.get('activities_image'),
            checkedActivities: solution.get('activities') || [],
            category: category.get('name'),
            mode: this.mode,
            activities: this.activities
        });
        this.renderMap('actors-map', solution.get('activities') || []);
        var okBtn = modal.querySelector('.confirm');
        if (this.viewer) this.viewer.destroy();
        this.viewer = new Viewer.default(modal);

        // add buttons and listeners for editing the solution in setup mode
        if (this.mode == 1){
            var nameInput = modal.querySelector('input[name="name"]'),
                stateImgInput = modal.querySelector('input[name="state-file"]'),
                effectImgInput = modal.querySelector('input[name="effect-file"]'),
                activitiesImgInput = modal.querySelector('input[name="activities-file"]'),
                descriptionArea = modal.querySelector('div[name="description"]'),
                activityInputs = modal.querySelectorAll('input[name="activity"]');

            $(descriptionArea).summernote({
                height: 300,
                maxHeight: null,
                //tooltip: false
            });

            stateImgInput.addEventListener('change', function(){
                swapImage(stateImgInput, 'state-image', 'currentstate_image');
            })
            effectImgInput.addEventListener('change', function(){
                swapImage(effectImgInput, 'effect-image', 'effect_image');
            })
            activitiesImgInput.addEventListener('change', function(){
                swapImage(activitiesImgInput, 'activities-image', 'activities_image');
            })

            for(var i = 0; i < activityInputs.length; i++){
                var checkbox = activityInputs[i];
                checkbox.addEventListener('change', function(event){
                    var id = event.target.value;
                    if (event.target.checked)
                        _this.renderActivityOnMap(id);
                    else
                        _this.removeActivityFromMap(id);
                })
            }

            // on confirming the dialog save the solution and the ratios
            okBtn.addEventListener('click', function(){

                var activities = [];
                for (i = 0; i < activityInputs.length; i++) {
                    var input = activityInputs[i];
                    if (input.checked) activities.push(input.value)
                }
                var data = {
                    name: nameInput.value,
                    description: $(descriptionArea).summernote('code'),
                    solution_category: solution.get('solution_category'), // required by backend
                    activities: activities
                }
                for (file in changedImages){
                  data[file] = changedImages[file];
                }
                _this.loader.activate()
                solution.save(data, {
                    success: function(){
                        $(modal).modal('hide');
                        _this.loader.deactivate();
                        if (onConfirm) onConfirm();
                    },
                    error: _this.onError,
                    patch: true
                })
            });
        }
        else okBtn.addEventListener('click', function(){ $(modal).modal('hide'); });

        // update map, when tab 'Actors' becomes active, else you won't see any map
        var actorsLink = modal.querySelector('a[href="#actors-tab"]');
        $(actorsLink).on('shown.bs.tab', function () {
            _this.map.map.updateSize();
        });
        $(modal).modal('show');
    },

    /*
    * render a map containing the administrative locations of actors of the given
    * activities
    */
    renderMap: function(divid, activities){
        var _this = this;
        // remove old map
        if (this.map){
            this.map.close();
            this.map = null;
        }
        var el = document.getElementById(divid),
            height = document.body.clientHeight * 0.6;
        el.style.height = height + 'px';
        this.map = new Map({
            el: el,
        });
        var focusarea = this.caseStudy.get('properties').focusarea;

        this.map.addLayer('background', {
            stroke: '#aad400',
            fill: 'rgba(170, 212, 0, 0.1)',
            strokeWidth: 1,
            zIndex: 0
        });
        // add polygon of focusarea to both maps and center on their centroid
        if (focusarea != null){
            var poly = this.map.addPolygon(focusarea.coordinates[0], {
                projection: this.projection,
                layername: 'background',
                tooltip: gettext('Focus area')
            });
            this.map.centerOnPolygon(poly, { projection: this.projection });
        };
        var deferreds = [];

        activities.forEach(function(activityId){
            _this.renderActivityOnMap(activityId);
        })
    },

    addToLegend: function(activityId, color){
        var legend = this.el.querySelector('#legend'),
            itemsDiv = legend.querySelector('.items'),
            legendDiv = document.createElement('li'),
            square = document.createElement('div'),
            textDiv = document.createElement('div'),
            head = document.createElement('b'),
            img = document.createElement('img'),
            activity = this.activities.get(activityId);
        legendDiv.dataset['id'] = activityId;
        textDiv.innerHTML = activity.get('name');
        textDiv.style.overflow = 'hidden';
        textDiv.style.textOverflow = 'ellipsis';
        legendDiv.appendChild(square);
        legendDiv.appendChild(textDiv);
        square.style.backgroundColor = color;
        square.style.float = 'left';
        square.style.width = '20px';
        square.style.height = '20px';
        square.style.marginRight = '5px';
        itemsDiv.appendChild(legendDiv);
    },

    removeFromLegend: function(activityId){
        var legend = this.el.querySelector('#legend'),
            itemsDiv = legend.querySelector('.items');
            entry = itemsDiv.querySelector('li[data-id="' + activityId + '"]');
        itemsDiv.removeChild(entry);
    },

    // render the administrative locations of all actors of activity with given id
    renderActivityOnMap: function(activityId){
        var _this = this,
            activity = this.activities.get(activityId);
        if (!activity) return;
        var activityName = activity.get('name'),
            checkList = document.getElementById('activities-checks');
        if (checkList){
            var loader = new utils.Loader(document.getElementById('activities-checks'), {disable: true});
            loader.activate();
        }
        var actors = new GDSECollection([], {
            apiTag: 'actors',
            apiIds: [this.caseStudy.id, this.keyflowId]
        })
        var color = utils.colorByName(activity.get('name')),
            layername = 'actors' + activityId;
        _this.map.addLayer(layername, {
            stroke: 'black',
            fill: color,
            strokeWidth: 1,
            zIndex: 1
        });
        actors.fetch({
            data: { activity: activityId, included: "True" },
            success: function(){
                if (actors.length === 0) {
                    if(loader) loader.deactivate();
                    return;
                }
                var actorIds = actors.pluck('id'),
                    locations = new GeoLocations([],{
                        apiTag: 'adminLocations',
                        apiIds: [_this.caseStudy.id, _this.keyflowId]
                    });
                var data = {};
                data['actor__in'] = actorIds.toString();
                locations.fetch({
                    data: data,
                    success: function(){
                        locations.forEach(function(loc){
                            var properties = loc.get('properties'),
                                actor = actors.get(properties.actor),
                                geom = loc.get('geometry');
                            if (geom) {
                                _this.map.addGeometry(geom.get('coordinates'), {
                                    projection: _this.projection,
                                    layername: layername,
                                    tooltip: activityName + '<br>' + actor.get('name'),
                                    type: 'Point'
                                });
                            }
                        })
                        if(loader) loader.deactivate();
                    }
                })
            }
        })
        this.addToLegend(activityId, color);
    },

    // remove the actors of activity with given id from map
    removeActivityFromMap: function(activityId){
        this.map.removeLayer('actors' + activityId);
        this.removeFromLegend(activityId);
    },

    /*
    * render a solution category panel
    * adds buttons in setup mode only
    */
    renderCategory: function(category){
        var _this = this;
        var panelList = this.el.querySelector('#categories');
        // create the panel (ToDo: use template for panels instead?)
        var div = document.createElement('div'),
            panel = document.createElement('div');
        div.classList.add('item-panel', 'bordered');
        div.style.minWidth = '300px';
        var label = document.createElement('label'),
            button = document.createElement('button'),
            editBtn = document.createElement('button'),
            removeBtn = document.createElement('button');
        label.innerHTML = category.get('name');
        label.style.marginBottom = '20px';

        panelList.appendChild(div);
        if (this.mode != 0){

            removeBtn.classList.add("btn", "btn-warning", "square", "remove");
            removeBtn.style.float = 'right';
            var span = document.createElement('span');
            removeBtn.title = gettext('Remove category')
            span.classList.add('glyphicon', 'glyphicon-minus');
            removeBtn.appendChild(span);
            removeBtn.addEventListener('click', function(){
                var message = gettext('Do you really want to delete the category and all its solutions?');
                _this.confirm({ message: message, onConfirm: function(){
                    category.destroy({
                        success: function() { panelList.removeChild(div); },
                        error: _this.onError
                    })
                }});
            })

            editBtn.classList.add("btn", "btn-primary", "square", "inverted");
            editBtn.style.float = 'right';
            editBtn.style.marginRight = '3px';
            var span = document.createElement('span');
            editBtn.title = gettext('Edit category')
            span.classList.add('glyphicon', 'glyphicon-pencil');
            editBtn.appendChild(span);
            editBtn.addEventListener('click', function(){
                _this.editCategory(category);
            })

            button.classList.add("btn", "btn-primary", "square", "add");
            span = document.createElement('span');
            span.classList.add('glyphicon', 'glyphicon-plus');
            button.innerHTML = gettext('Solution');
            button.title = gettext('Add solution to category');
            button.insertBefore(span, button.firstChild);
            button.addEventListener('click', function(){
                _this.addSolution(panel, category);
            })
            div.appendChild(removeBtn);
            div.appendChild(editBtn);
        }
        div.appendChild(label);
        div.appendChild(panel);
        if (this.mode != 0) div.appendChild(button);
        // add the items
        if (category.solutions){
            category.solutions.forEach(function(solution){
                _this.renderSolutionItem(panel, solution);
            });
        }
    },

    /*
    * render a solution item in the panel
    */
    renderSolutionItem: function(panel, solution){
        var _this = this;
        // render panel item from template (in templates/common.html)
        var html = document.getElementById('panel-item-template').innerHTML,
            template = _.template(html);
        var panelItem = document.createElement('div');
        panelItem.classList.add('panel-item');
        panelItem.classList.add('noselect');
        panelItem.innerHTML = template({ name: solution.get('name') });
        panel.appendChild(panelItem);
        // in workshop mode show solution on click on panel, else on click on edit
        var editBtn = (this.mode == 0) ? panelItem: panelItem.querySelector('.edit'),
            removeBtn = panelItem.querySelector('.remove');
        editBtn.addEventListener('click', function(){
            _this.showSolution(solution);
        })
        removeBtn.addEventListener('click', function(){
            var message = gettext('Do you really want to delete the solution?');
            _this.confirm({ message: message, onConfirm: function(){
                solution.destroy({
                    success: function() { panel.removeChild(panelItem); },
                    error: _this.onError
                })
            }});
        })
    },

    /*
    * add a solution category and save it
    */
    addCategory: function(){
        var _this = this;
        function onConfirm(name){
            var category = _this.categories.create(
                { name: name }, {
                success: function(){
                    category.solutions = new GDSECollection([], {
                        apiTag: 'solutions',
                        apiIds: [_this.caseStudy.id, _this.keyflowId, category.id]
                    });
                        _this.categories.add(category);
                        _this.renderCategory(category);
                    },
                    error: _this.onError
                }
            )
        }
        _this.getName({ onConfirm: onConfirm });
    },

    editCategory: function(category){
        var _this = this;
        function onConfirm(name){
            category.save(
                {
                    name: name,
                },
                {
                    success: _this.render,
                    error: _this.onError,
                    wait: true
                }
            );
        }
        this.getName({
            title: gettext('Edit Category'),
            name: category.get('name'),
            onConfirm: onConfirm
        })
    },

    /*
    * add a solution and save it
    */
    addSolution: function(panel, category){
        var _this = this,
            solutions = category.solutions;
        function onConfirm(name){
            var solution = solutions.create(
                {
                    name: name,
                    solution_category: category.id,
                    description: '-',
                    activities: []
                },
                {
                    wait: true,
                    success: function(){
                        _this.renderSolutionItem(panel, solution);
                    },
                    error: _this.onError
                }
            )
        };
        this.getName({
            title: gettext('Add Solution'),
            onConfirm: onConfirm
        });
    },

    toggleFullscreen: function(event){
        event.target.parentElement.classList.toggle('fullscreen');
    }

});
return SolutionsView;
}
);
