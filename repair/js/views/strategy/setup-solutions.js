define(['views/common/baseview', 'underscore', 'collections/gdsecollection',
        'collections/geolocations', 'visualizations/map', 'viewerjs', 'app-config',
        'utils/utils', 'summernote', 'summernote/dist/summernote.css',
        'bootstrap', 'viewerjs/dist/viewer.css', 'bootstrap-select'],

function(BaseView, _, GDSECollection, GeoLocations, Map, Viewer, config,
         utils, summernote){
/**
*
* @author Christoph Franke
* @name module:views/SolutionsSetupView
* @augments BaseView
*/
var SolutionsSetupView = BaseView.extend(
    /** @lends module:views/SolutionsSetupView.prototype */
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
        SolutionsSetupView.__super__.initialize.apply(this, [options]);
        var _this = this;

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
            apiIds: [this.caseStudy.id, this.keyflowId],
            comparator: 'name'
        });

        var promises = [];
        promises.push(this.categories.fetch());
        promises.push(this.solutions.fetch());

        this.loader.activate();
        Promise.all(promises).then(function(){
            _this.solutions.sort();
            _this.loader.deactivate();
            _this.render();
        });
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'click #add-solution': 'addSolution',
        'click #edit-solution-categories': 'showCategoryModal'
    },

    /*
    * render the view
    */
    render: function(){
        var _this = this,
            html = document.getElementById(this.template).innerHTML,
            template = _.template(html);
        this.el.innerHTML = template({solutions: this.solutions});
        var promises = [];
        this.solutionSelect = this.el.querySelector('#solution-select');
        this.categorySelect = this.el.querySelector('#solution-category');
        $(this.solutionSelect).selectpicker({size: 10});
        this.populateSolutions();
        this.populateCategories();

        this.nameInput = this.el.querySelector('input[name="name"]');
        this.descriptionArea = this.el.querySelector('div[name="description"]');
        this.stateImgInput = this.el.querySelector('input[name="state-file"]');
        this.effectImgInput = this.el.querySelector('input[name="effect-file"]');
        this.activitiesImgInput = this.el.querySelector('input[name="activities-file"]');
        this.stateImg = this.el.querySelector('#state-image');
        this.effectImg = this.el.querySelector('#effect-image');
        this.activitiesImg = this.el.querySelector('#activities-image');

        $(this.descriptionArea).summernote({
            height: 600,
            maxHeight: null
        });

        this.el.querySelector('#edit-solution').addEventListener('click', function(){
            _this.activeSolution = _this.solutions.get(_this.solutionSelect.value);
            _this.renderSolution(_this.activeSolution);
        });

        this.el.querySelector('#save-solution').addEventListener('click', function(){
            _this.saveSolution(_this.activeSolution);
        });

        this.swappedImages = {};

        function swapImage(input, img, field){
            if (input.files && input.files[0]){
                var reader = new FileReader();
                reader.onload = function (e) {
                    img.src = e.target.result;
                };
                reader.readAsDataURL(input.files[0]);
                _this.swappedImages[field] = input.files[0];
            }
        }

        this.stateImgInput.addEventListener('change', function(){
            swapImage(_this.stateImgInput, _this.stateImg, 'currentstate_image');
        })
        this.effectImgInput.addEventListener('change', function(){
            swapImage(_this.effectImgInput, _this.effectImg, 'effect_image');
        })
        this.activitiesImgInput.addEventListener('change', function(){
            swapImage(_this.activitiesImgInput, _this.activitiesImg, 'activities_image');
        })

        this.viewer = new Viewer.default(this.el);

        // rerender categories after editing
        this.catModal = this.el.querySelector('#categories-modal');
        $(this.catModal).on('hidden.bs.modal', function () {
            _this.populateSolutions();
            _this.populateCategories();
        })
    },

    /* fill selection with solutions */
    populateSolutions: function(){
        var _this = this,
            prevSel = this.solutionSelect.value;
        utils.clearSelect(this.solutionSelect);
        this.categories.forEach(function(category){
            var group = document.createElement('optgroup'),
                solutions = _this.solutions.filterBy({solution_category: category.id});
            group.label = category.get('name');
            solutions.forEach(function(solution){
                var option = document.createElement('option');
                option.value = solution.id;
                option.text = solution.get('name');
                group.appendChild(option);
            })
            _this.solutionSelect.appendChild(group);
        })
        if (prevSel != null) this.solutionSelect.value = prevSel;
        $(this.solutionSelect).selectpicker('refresh');
    },

    /* fill selection with solutions */
    populateCategories: function(){
        var _this = this,
            prevSel = this.categorySelect.value;
        utils.clearSelect(this.categorySelect);
        this.categories.forEach(function(category){
            var option = document.createElement('option');
            option.value = category.id;
            option.text = category.get('name');
            _this.categorySelect.appendChild(option);
        })
        if (prevSel != null) this.categorySelect.value = prevSel;
    },

    renderSolution: function(solution){
        var _this = this;
        if (!solution) return;
        this.el.querySelector('#solution-edit-content').style.display = 'block';
        this.swappedImages = {};
        this.nameInput.value = solution.get('name');
        this.categorySelect.value = solution.get('solution_category');
        $(this.descriptionArea).summernote("code", solution.get('description'));
        this.effectImg.src = solution.get('effect_image');
        this.stateImg.src = solution.get('currentstate_image');
        this.activitiesImg.src = solution.get('activities_image');
    },

    saveSolution: function(solution){
        var _this = this;
        var data = {
            name: this.nameInput.value,
            description: $(this.descriptionArea).summernote('code'),
            solution_category: this.categorySelect.value
        }
        for (var file in this.swappedImages){
          data[file] = _this.swappedImages[file];
        }
        _this.loader.activate()
        solution.save(data, {
            success: function(){
                _this.loader.deactivate();
                // group might have changed -> update solution list
                _this.populateSolutions();
                _this.alert(gettext('Upload successful'), gettext('Success'));
            },
            error: _this.onError,
            patch: true
        })

    },

    /*
    * open a modal for editing the categories
    */
    showCategoryModal: function(){
        var _this = this;
            html = document.getElementById('categories-template').innerHTML,
            template = _.template(html);

        this.catModal.innerHTML = template({
            keyflowName: this.keyflowName
        });

        var catList = this.catModal.querySelector('.category-list');


        function editCategory(category, catItem){
            _this.getName({
                name: category.get('name'),
                onConfirm: function(name){
                    category.save(
                        {
                            name: name
                        },
                        {
                            error: _this.onError,
                            success: function(){
                                catItem.querySelector('label').innerHTML = name;
                            },
                            patch: true
                        }
                    )
                }
            })
        }

        function removeCategory(category, catItem){
            var message = gettext('Do you really want to delete the category and all its solutions?');
            _this.confirm({ message: message, onConfirm: function(){
                category.destroy({
                    success: function() { catList.removeChild(catItem); },
                    wait: true,
                    error: _this.onError
                })
            }});
        }

        function addCategoryItem(category){
            var catItem = document.createElement('div'),
                html = document.getElementById('panel-item-template').innerHTML,
                template = _.template(html);
            catItem.classList.add('panel-item');
            catItem.classList.add('noselect');
            catItem.innerHTML = template({ name: category.get('name') });
            catList.appendChild(catItem);
            catItem.querySelector('.edit').addEventListener('click', function(){
                editCategory(category, catItem);
            })
            catItem.querySelector('.remove').addEventListener('click', function(){
                removeCategory(category, catItem);
            })
        }

        function addCategory(){
            function onConfirm(name){
                var category = _this.categories.create(
                    { name: name }, {
                        success: function(){
                            addCategoryItem(category);
                        },
                        error: _this.onError
                    }
                )
            }
            _this.getName({ onConfirm: onConfirm })
        }


        this.categories.forEach(addCategoryItem);

        this.catModal.querySelector('.add').addEventListener('click', addCategory);
        $(this.catModal).modal('show');
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
                    documentation: '-'
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
return SolutionsSetupView;
}
);
