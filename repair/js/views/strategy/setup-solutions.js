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

        this.solutions = options.solutions;
        this.categories = options.categories;

        var promises = [];

        this.render();
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'click #add-solution': 'showAddSolution',
        'click #delete-solution': 'removeSolution',
        'click #add-solution-modal .confirm': 'addSolution',
        'click button[name="edit-solution-categories"]': 'showCategoryModal',
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
        this.content = this.el.querySelector('#solution-edit-content');
        this.solutionSelect = this.el.querySelector('select[name="solutions"]');
        this.categorySelect = this.content.querySelector('select[name="solution-category"]');
        this.newSolutionModal = this.el.querySelector('#add-solution-modal');
        this.newSolutionCategorySelect = this.newSolutionModal.querySelector('select[name="solution-category"]');
        $(this.solutionSelect).selectpicker({size: 10});
        this.populateSolutions();
        this.populateCategories(this.categorySelect);
        this.populateCategories(this.newSolutionCategorySelect);
        this.editSolutionBtn = this.el.querySelector('#edit-solution')

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

        this.editSolutionBtn.addEventListener('click', function(){
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

        this.catModal = this.el.querySelector('#categories-modal');
        // rerender categories after editing
        $(this.catModal).on('hidden.bs.modal', function () {
            _this.populateSolutions();
            _this.populateCategories(_this.categorySelect);
            _this.populateCategories(_this.newSolutionCategorySelect);
        })
    },

    /* fill selection with solutions */
    populateSolutions: function(selected){
        var _this = this,
            prevSel = selected || this.solutionSelect.value;
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
    populateCategories: function(el){
        var _this = this,
            prevSel = el.value;
        utils.clearSelect(el);
        this.categories.forEach(function(category){
            var option = document.createElement('option');
            option.value = category.id;
            option.text = category.get('name');
            el.appendChild(option);
        })
        if (prevSel != null) el.value = prevSel;
    },

    renderSolution: function(solution){
        var _this = this;
        if (!solution) return;
        this.content.style.display = 'block';
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
            var message = gettext('Do you want to delete the category?');
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
    showAddSolution: function(){
        var _this = this,
            confirmBtn = this.newSolutionModal.querySelector('.confirm');;
        $(this.newSolutionModal).modal('show');
    },

    addSolution: function(){
        var _this = this,
            name = this.newSolutionModal.querySelector('input[name="name"]').value,
            category = this.newSolutionCategorySelect.value;
        var solution = _this.solutions.create(
            {
                name: name,
                solution_category: category,
                description: '-',
                documentation: '-'
            },
            {
                wait: true,
                success: function(){
                    $(_this.newSolutionModal).modal('hide');
                    _this.populateSolutions(solution.id);
                    _this.editSolutionBtn.click();
                },
                error: _this.onError
            }
        )
    },

    removeSolution: function(){
        var _this = this,
            solution = this.solutions.get(this.solutionSelect.value);
        if (!solution) return;
        var message = gettext('Do you want to delete the selected solution?');
        this.confirm({ message: message, onConfirm: function(){
            solution.destroy({
                success: function() {
                    if (_this.activeSolution == solution)
                        _this.content.style.display = 'none';
                    _this.populateSolutions();
                },
                wait: true,
                error: _this.onError
            })
        }});
    },

    toggleFullscreen: function(event){
        event.target.parentElement.classList.toggle('fullscreen');
    }

});
return SolutionsSetupView;
}
);
