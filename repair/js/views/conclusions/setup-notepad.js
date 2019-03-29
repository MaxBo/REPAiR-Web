
define(['underscore','views/common/baseview', 'collections/gdsecollection',
        'muuri'],

function(_, BaseView, GDSECollection, Muuri){
    /**
    *
    * @author Christoph Franke, Balázs Dukai
    * @name module:views/SetupNotepadView
    * @augments Backbone.View
    */
    var SetupNotepadView = BaseView.extend(
        /** @lends module:views/SetupNotepadView.prototype */
        {

        /**
        * render setup view on consensus levels and sections used in conclusions notepad
        *
        * @param {Object} options
        * @param {HTMLElement} options.el                          element the view will be rendered in
        * @param {string} options.template                         id of the script element containing the underscore template to render this view
        * @param {module:models/CaseStudy} options.caseStudy       the casestudy to add levels and sections to
        *
        * @constructs
        * @see http://backbonejs.org/#View
        */
        initialize: function(options){
            SetupNotepadView.__super__.initialize.apply(this, [options]);
            var _this = this;

            this.template = options.template;
            this.caseStudy = options.caseStudy;

            this.loader.activate();
            var promises = [this.consensusLevels.fetch(), this.sections.fetch()]
            Promise.all(promises).then(function(){
                _this.loader.deactivate();
                _this.consensusLevels.sort();
                _this.sections.sort();
                _this.render();
            })
        },

        /*
        * dom events (managed by jquery)
        */
        events: {
            'click .add': 'addModel'
        },

        /*
        * render the view
        */
        render: function(){
            var consensusPanel = document.getElementById('consenus-levels').querySelector('.item-panel');
            var sectionsPanel = document.getElementById('sections').querySelector('.item-panel');

            this.consensusGrid = this.renderGrid(consensusPanel, this.consensusLevels);
            this.sectionsGrid = this.renderGrid(sectionsPanel, this.sections);

        },

        renderGrid: function(panel, collection){
            var _this = this;

            var grid = new Muuri(panel, {
                items: '.panel-item',
                dragAxis: 'y',
                layoutDuration: 400,
                layoutEasing: 'ease',
                dragEnabled: true,
                dragSortInterval: 0,
                dragReleaseDuration: 400,
                dragReleaseEasing: 'ease'
            })
            grid.on('dragReleaseEnd', function () {
                _this.uploadPriorities(grid, collection) } );

            collection.forEach(function(model){
                _this.renderItem(grid, model);
            });
            return grid;
        },

        uploadPriorities(grid, collection){
            var items = grid.getItems(),
                priority = 0;
            items.forEach(function(item){
                var id = item.getElement().dataset.id,
                    model = collection.get(id);
                model.set('priority', priority);
                model.save();
                priority++;
            })
        },

        renderItem(grid, model){
            var html = document.getElementById('panel-item-template').innerHTML,
                template = _.template(html),
                panelItem = document.createElement('div'),
                itemContent = document.createElement('div'),
                _this = this;
            panelItem.classList.add('panel-item');
            panelItem.classList.add('draggable');
            panelItem.style.position = 'absolute';
            panelItem.dataset.id = model.id;
            itemContent.classList.add('noselect', 'item-content');
            itemContent.innerHTML = template({ name: model.get('name') });
            var editBtn = itemContent.querySelector("button.edit");
            var removeBtn = itemContent.querySelector("button.remove");
            editBtn.addEventListener('click', function(){
                _this.editPanelItem(panelItem, model);
            });
            removeBtn.addEventListener('click', function(){
                _this.removePanelItem(panelItem, model, grid);
            });
            panelItem.appendChild(itemContent);
            grid.add(panelItem);
        },

        addModel: function(evt){
            var _this = this,
                button = evt.target,
                type = button.dataset['type'],
                grid = this.consensusGrid;

            var grid = (type == 'consensus') ? this.consensusGrid: this.sectionsGrid,
                collection = (type == 'consensus') ? this.consensusLevels: this.sections;

            function onConfirm(name){
                var model = collection.create(
                    { name: name },
                    {
                        success: function(){
                            _this.renderItem(grid, model);
                            _this.uploadPriorities(grid, collection);
                        },
                        error: _this.onError,
                        wait: true
                    }
                );
            }
            this.getName({
                onConfirm: onConfirm
            })
        },

        editPanelItem: function(item, model){
            var _this = this,
                id = item.id,
                title = gettext("Edit");
            function onConfirm(name){
                model.save({ name: name }, {
                    success: function(){
                        var label = item.querySelector('label');
                        label.innerHTML = name;
                    },
                    error: _this.onError
                });
            }
            this.getName({
                name: model.get('name'),
                onConfirm: onConfirm
            })
        },

        removePanelItem: function(item, model, grid){
            var _this = this,
                message = gettext("Do you want to delete the item?");
            function onConfirm(name){
                model.destroy({
                    success: function(){
                        grid.remove(item, { removeElements: true });
                    },
                    error: _this.onError
                });
            }
            this.confirm({
                message: gettext("Do you want to delete the selected item?"),
                onConfirm: onConfirm
            })
        }
    });
    return SetupNotepadView;
}
);
