define(['views/common/baseview', 'underscore', 'collections/gdsecollection',
        'visualizations/map', 'app-config', 'utils/utils', 'bootstrap'],

function(BaseView, _, GDSECollection, Map, config, utils){
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
        _.bindAll(this, 'addSolutionQuanitityRow');
        _.bindAll(this, 'addSolutionRatioOneUnitRow');

        this.template = options.template;
        this.caseStudy = options.caseStudy;
        this.projection = 'EPSG:4326';
        this.mode = options.mode || 0;

        // ToDo: replace with collections fetched from server
        this.categories = new GDSECollection([], {
            apiTag: 'solutionCategories', apiIds: [this.caseStudy.id]
        }),

        this.loader.activate();
        this.keyflows = new GDSECollection([], {
            apiTag: 'keyflowsInCaseStudy', apiIds: [this.caseStudy.id]
        });
        var promises = [];
        this.units = new GDSECollection([], { apiTag: 'units' });
        this.keyflows.fetch({
            success: function(){
                promises.push(_this.categories.fetch());
                promises.push(_this.units.fetch());
                _this.keyflows.forEach(function(keyflow){
                    var activities = new GDSECollection([], {
                        apiTag: 'activities',
                        apiIds: [_this.caseStudy.id, keyflow.id]
                    })
                    promises.push(activities.fetch({
                        success: function(response){
                            keyflow.activities = response;
                        }
                    }));
                })

               Promise.all(promises).then(function(){
                    _this.loader.deactivate();
                    _this.render();
                });
            },
            error: function(res){
                _this.loader.deactivate();
                _this.onError(res);
            }
        })
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
        this.el.innerHTML = template({ mode: this.mode });
        var promises = [];
        this.categories.forEach(function(category){
            category.solutions = new GDSECollection([], {
                apiTag: 'solutions', apiIds: [_this.caseStudy.id, category.id]
            }),
            promises.push(category.solutions.fetch());
        });
        // fetch all before rendering to keep the order
        Promise.all(promises).then(function(){
            _this.categories.forEach(function(category){
                _this.renderCategory(category);
            });

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
    * adds a "Ratio defining one unit" to the "Units/Ratios" tab inside
    * the solution detail modal
    */
    addSolutionQuanitityRow: function(squantity){
        var table = document.getElementById('required-ratios'),
            row = table.insertRow(-1);

        var nameInput = document.createElement('input');
        row.insertCell(-1).appendChild(nameInput);
        nameInput.value = squantity.get('name');
        nameInput.classList.add('form-control');
        nameInput.addEventListener('change', function(){ squantity.set('name', nameInput.value); })

        var unitSelect = document.createElement('select');
        row.insertCell(-1).appendChild(unitSelect);
        this.units.forEach(function(unit){
            var option = document.createElement('option');
            option.value = unit.id;
            option.text = unit.get('name');
            unitSelect.appendChild(option);
        })
        unitSelect.value = squantity.get('unit');
        unitSelect.classList.add('form-control');
        unitSelect.addEventListener('change', function(){ squantity.set('unit', unitSelect.value); })

        var checkbox = document.createElement("input");
        checkbox.type = 'checkbox';
        row.insertCell(-1).appendChild(checkbox);

        checkbox.addEventListener('change', function() {
            row.classList.toggle('strikeout');
            row.classList.toggle('dsbld');
            squantity.markedForDeletion = checkbox.checked;
        });
    },

    /*
    * adds a "Ratio to be set when implementing this solution" to the "Units/Ratios" tab inside
    * the solution detail modal
    */
    addSolutionRatioOneUnitRow: function(sratio){
        var table = document.getElementById('one-unit-ratios'),
            row = table.insertRow(-1);

        var nameInput = document.createElement('input');
        row.insertCell(-1).appendChild(nameInput);
        nameInput.value = sratio.get('name');
        nameInput.classList.add('form-control');
        nameInput.addEventListener('change', function(){ sratio.set('name', nameInput.value); })

        var valueInput = document.createElement('input');
        valueInput.type = 'number';
        row.insertCell(-1).appendChild(valueInput);
        valueInput.value = sratio.get('value');
        valueInput.classList.add('form-control');
        valueInput.addEventListener('change', function(){ sratio.set('value', valueInput.value); })

        var unitSelect = document.createElement('select');
        row.insertCell(-1).appendChild(unitSelect);
        this.units.forEach(function(unit){
            var option = document.createElement('option');
            option.value = unit.id;
            option.text = unit.get('name');
            unitSelect.appendChild(option);
        })
        unitSelect.value = sratio.get('unit');
        unitSelect.classList.add('form-control');
        unitSelect.addEventListener('change', function(){ sratio.set('unit', unitSelect.value); })

        var checkbox = document.createElement("input");
        checkbox.type = 'checkbox';
        row.insertCell(-1).appendChild(checkbox);

        checkbox.addEventListener('change', function() {
            row.classList.toggle('strikeout');
            row.classList.toggle('dsbld');
            sratio.markedForDeletion = checkbox.checked;
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
        var squantities = new GDSECollection([], {
                apiTag: 'solutionQuantities',
                apiIds: [this.caseStudy.id, solution.get('solution_category'),
                         solution.id]
            }),

            sratios = new GDSECollection([], {
                apiTag: 'solutionRatioOneUnits',
                apiIds: [this.caseStudy.id, solution.get('solution_category'),
                         solution.id]
            });

        if (solution.id){
            squantities.fetch({success: function(){
                squantities.forEach(_this.addSolutionQuanitityRow)
            }});
            sratios.fetch({success: function(){
                sratios.forEach(_this.addSolutionRatioOneUnitRow)
            }});
        }

        var category = this.categories.get(solution.get('solution_category'));
        var html = document.getElementById('view-solution-template').innerHTML,
            template = _.template(html),
            modal = this.el.querySelector('#solution-modal');

        modal.innerHTML = template({
            name: solution.get('name'),
            description: solution.get('description'),
            unit: solution.get('one_unit_equals'),
            effectSrc: solution.get('effect_image'),
            stateSrc: solution.get('currentstate_image'),
            activitiesSrc: solution.get('activities_image'),
            checkedActivities: solution.get('activities'),
            category: category.get('name'),
            mode: this.mode,
            keyflows: this.keyflows
        });
        this.renderMap('actors-map', solution.get('activities'));
        var okBtn = modal.querySelector('.confirm');

        // add buttons and listeners for editing the solution in setup mode
        if (this.mode == 1){
            var nameInput = modal.querySelector('input[name="name"]'),
                unitInput = modal.querySelector('input[name="unit"]'),
                stateImgInput = modal.querySelector('input[name="state-file"]'),
                effectImgInput = modal.querySelector('input[name="effect-file"]'),
                activitiesImgInput = modal.querySelector('input[name="activities-file"]'),
                descriptionArea = modal.querySelector('textarea[name="description"]'),
                activityInputs = modal.querySelectorAll('input[name="activity"]'),
                addRatioBtn = modal.querySelector('#add-one-unit-ratio'),
                addQuantityBtn = modal.querySelector('#add-required-ratio');

            stateImgInput.addEventListener('change', function(){
                swapImage(stateImgInput, 'state-image', 'currentstate_image');
            })
            effectImgInput.addEventListener('change', function(){
                swapImage(effectImgInput, 'effect-image', 'effect_image');
            })
            activitiesImgInput.addEventListener('change', function(){
                swapImage(activitiesImgInput, 'activities-image', 'activities_image');
            })

            addQuantityBtn.addEventListener('click', function(){
                squantity = new squantities.model({
                    name: '', unit: _this.units.first().id
                })
                squantities.add(squantity);
                _this.addSolutionQuanitityRow(squantity);
            })
            addRatioBtn.addEventListener('click', function(){
                sratio = new sratios.model({
                    name: '', unit: _this.units.first().id, value: 0
                })
                sratios.add(sratio);
                _this.addSolutionRatioOneUnitRow(sratio);
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
                    one_unit_equals: unitInput.value,
                    description: descriptionArea.value,
                    solution_category: solution.get('solution_category'), // required by backend
                    activities: activities
                }
                console.log(changedImages)
                for (file in changedImages){
                  data[file] = changedImages[file];
                }
                solution.save(data, {
                    success: function(){
                        var ratioModels = [];
                        squantities.forEach(function(m) {ratioModels.push(m)});
                        sratios.forEach(function(m) {ratioModels.push(m)});

                        utils.queuedUpload(ratioModels, {
                            success: function(){
                                $(modal).modal('hide');
                                if (onConfirm) onConfirm();
                            },
                            error: function(m, r){ _this.onError(r) }
                        });
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

    // search for the keyflow of an activity
    getKeyflow: function(activityId){
        var keyflow = this.keyflows.find(function(keyflow){
            var found = keyflow.activities.find(function(activity){
                return activity.id == activityId;
            });
            return found != null;
        })
        return keyflow;
    },

    // render the administrative locations of all actors of activity with given id
    renderActivityOnMap: function(activityId){
        var _this = this;
        var keyflowId = this.getKeyflow(activityId).id,
            actorUrl = config.api.actors.format(this.caseStudy.id, keyflowId);
        var checkList = document.getElementById('activities-checks');
        if (checkList){
            var loader = new utils.Loader(document.getElementById('activities-checks'), {disable: true});
            loader.activate();
        }
        // fetch them as json instead of a collection, reduces unnessecary memory overhead
        $.ajax({
            url: actorUrl,
            type: "GET",
            dataType: "json",
            data: { activity: activityId, page_size: 100000, included: "True" },
            success: function(response){
                if (checkList) loader.deactivate();
                var actorIds = [];
                response.results.forEach(function(actor){ actorIds.push(actor.id) });
                if (actorIds.length > 0){
                    var adminLocUrl = config.api.adminLocations.format(_this.caseStudy.id, keyflowId);
                    adminLocUrl += '?actor__in=' + actorIds.toString();
                    _this.map.addLayer('actors' + activityId, {
                        source: {
                            url: adminLocUrl
                        }
                    })
                }
            }
        })
    },

    // remove the actors of activity with given id from map
    removeActivityFromMap: function(activityId){
        this.map.removeLayer('actors' + activityId);
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
            removeBtn = document.createElement('button');
        label.innerHTML = category.get('name');
        label.style.marginBottom = '20px';

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

        button.classList.add("btn", "btn-primary", "square", "add");
        span = document.createElement('span');
        span.classList.add('glyphicon', 'glyphicon-plus');
        button.innerHTML = gettext('Solution');
        button.title = gettext('Add solution to category');
        button.insertBefore(span, button.firstChild);
        button.addEventListener('click', function(){
            _this.addSolution(panel, category);
        })

        panelList.appendChild(div);
        div.appendChild(removeBtn);
        div.appendChild(label);
        div.appendChild(panel);
        div.appendChild(button);
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
            var category = _this.categories.create( { name: name }, {success: function(){
                category.solutions = new GDSECollection([], {
                    apiTag: 'solutions',
                    apiIds: [_this.caseStudy.id, category.id]
                });
                    _this.categories.add(category);
                    _this.renderCategory(category);
                },
                error: _this.onError
            })
        }
        _this.getName({ onConfirm: onConfirm });
    },

    /*
    * add a solution and save it
    */
    addSolution: function(panel, category){
        var _this = this;
        var solutions = category.solutions,
            solution = new solutions.model(
                { name: name, solution_category: category.id },
            );
        function onConfirm(){
            solutions.add(solution);
            _this.renderSolutionItem(panel, solution);
        }
        _this.showSolution(solution, onConfirm);
    },

    toggleFullscreen: function(event){
        event.target.parentElement.classList.toggle('fullscreen');
    }
});
return SolutionsView;
}
);
