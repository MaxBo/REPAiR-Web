define(['views/common/baseview', 'views/common/filter-flows',
        'collections/gdsecollection', 'underscore'],

function(BaseView, FilterFlowsView, GDSECollection, _){
/**
*
* @author Christoph Franke
* @name module:views/FlowsSetupView
* @augments module:views/BaseView
*/
var FlowsSetupView = BaseView.extend(
    /** @lends module:views/FlowsSetupView.prototype */
    {

    /**
    * render view to show keyflows in casestudy
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
        FlowsSetupView.__super__.initialize.apply(this, [options]);
        this.caseStudy = options.caseStudy;
        this.keyflowId = options.keyflowId;
        this.filters = new GDSECollection([], {
            apiTag: 'flowFilters',
            apiIds: [this.caseStudy.id, this.keyflowId],
            comparator: 'name'
        })
        this.loader.activate();
        this.filters.fetch({
            success: function(){
                _this.loader.deactivate();
                _this.render();
            },
            error: _this.onError
        })
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'click #edit-flowfilter-button': 'editFilter',
        'click #new-flowfilter-button': 'createFilter',
        'click #upload-flowfilter-button': 'uploadFilter',
        'click #delete-flowfilter-button': 'deleteFilter'
    },

    /*
    * render the view
    */
    render: function(){
        var _this = this,
            html = document.getElementById(this.template).innerHTML,
            template = _.template(html);
        this.el.innerHTML = template({ filters: this.filters });
        this.toggleVisibility(false);
        this.renderFilterFlowsView();
        this.flowFilterSelect = this.el.querySelector('select[name="filter"]');
        this.nameInput = this.el.querySelector('input[name="name"]');
        this.descriptionInput = this.el.querySelector('textarea[name="description"]');
    },

    renderFilterFlowsView: function(){
        var el = this.el.querySelector('#setup-flows-content'),
            _this = this;
        this.loader.activate();
        this.filterFlowsView = new FilterFlowsView({
            caseStudy: this.caseStudy,
            el: el,
            template: 'filter-flows-template',
            keyflowId: this.keyflowId,
            callback: function(){
                _this.loader.deactivate();
                // expand filter section
                _this.el.querySelector('#toggle-filter-section').click();
            }
        })
    },

    createFilter: function(){
        this.toggleVisibility(true);
        var _this = this;
        function create(name){
            var filter = _this.filters.create(
                { name: name },
                { success: function(){
                    var option = document.createElement('option');
                    option.value = filter.id;
                    option.innerHTML = filter.get('name');
                    _this.nameInput.value = filter.get('name');
                    _this.descriptionInput.value = filter.get('description');
                    _this.flowFilterSelect.appendChild(option);
                    _this.flowFilterSelect.value = filter.id;
                    _this.filterFlowsView.applyFilter(filter);
                    _this.filter = filter;
                }, error: _this.onError, wait: true }
            );
        }
        this.getName({ onConfirm: create });
    },

    uploadFilter: function(){
        var selected = this.flowFilterSelect.value,
            filter = this.filter,
            _this = this;
        this.filterFlowsView.getFilter(filter);
        filter.set('name', this.nameInput.value);
        filter.set('description', this.descriptionInput.value);
        filter.save(null, {
            success: function(model){
                // update name in select
                var option = _this.flowFilterSelect.querySelector('option[value="'+model.id+'"]');
                option.innerHTML = model.get('name');
                _this.alert(gettext('Upload successful'), gettext('Success'));
            },
            error: this.onError
        });
    },

    toggleVisibility(on){
        var visibility = (on) ? 'visible': 'hidden';
        this.el.querySelector('#setup-flows-content').style.visibility = visibility;
        this.el.querySelector('#filter-attributes').style.visibility = visibility;
    },

    editFilter: function(){
        var selected = this.flowFilterSelect.value,
            filter = this.filters.get(selected);
        if (!filter) return;
        this.filter = filter;
        this.toggleVisibility(true);
        this.nameInput.value = filter.get('name');
        this.descriptionInput.value = filter.get('description');

        this.filterFlowsView.applyFilter(filter);
    },

    // delete selected filter
    deleteFilter: function(){
        var selected = this.flowFilterSelect.value,
            filter = this.filters.get(selected),
            id = filter.id
            _this = this;
        if (!filter) return;
        function destroy(){
            if (filter == _this.filter)
                _this.toggleVisibility(false);
            filter.destroy({
                success: function(){
                    var option = _this.flowFilterSelect.querySelector('option[value="' + id + '"]');
                    _this.flowFilterSelect.removeChild(option);
                },
                error: _this.onError
            });
        };
        this.confirm({
            message: gettext('Do you want to delete the Filter') + ' "' + filter.get('name') + '"?',
            onConfirm: destroy
        })
    },

    close: function(){
        if (this.filterFlowsView) this.filterFlowsView.close();
        FlowsSetupView.__super__.close.call(this);
    }

});
return FlowsSetupView;
}
);

