define(['views/baseview', 'underscore', 'models/actor', 'collections/activities',
    'collections/actors', 'collections/arealevels', 'views/data-entry/edit-actor',
    'utils/loader', 'app-config', 'datatables.net', 'bootstrap-select'],
function(BaseView, _, Actor, Activities, Actors, AreaLevels, EditActorView, 
    Loader, config){

/**
    *
    * @author Christoph Franke
    * @name module:views/ActorsView
    * @augments module:views/BaseView
    */
var ActorsView = BaseView.extend(
    /** @lends module:views/ActorsView.prototype */
    {

    /**
    * render view to edit the actors of a keyflow
    *
    * @param {Object} options
    * @param {HTMLElement} options.el                     element the view will be rendered in
    * @param {string} options.template                    id of the script element containing the underscore template to render this view
    * @param {module:collections/Keyflows.Model}          options.model the keyflow the actors belong to
    * @param {module:models/CaseStudy} options.caseStudy  the casestudy the keyflow belongs to
    *
    * @constructs
    * @see http://backbonejs.org/#View
    */
    initialize: function(options){
        _.bindAll(this, 'render');
        _.bindAll(this, 'removeActor');
        var _this = this;

        this.template = options.template;
        var keyflowId = this.model.id,
            caseStudyId = this.model.get('casestudy');

        this.activities = new Activities([], { caseStudyId: caseStudyId, keyflowId: keyflowId });
        this.actors = new Actors([], { 
            caseStudyId: caseStudyId, keyflowId: keyflowId,
            state: {
                pageSize: 1000000,
                firstPage: 1,
                currentPage: 1
            } 
        });
        this.areaLevels = new AreaLevels([], { caseStudyId: caseStudyId })
        this.showAll = true;
        this.caseStudy = options.caseStudy;
        this.caseStudyId = this.model.get('casestudy');

        var loader = new Loader(document.getElementById('actors-edit'),
            {disable: true});

        this.projection = 'EPSG:4326'; 

        var Reasons = Backbone.Collection.extend({url: config.api.reasons});
        this.reasons = new Reasons([]);

        $.when(
            this.activities.fetch(), 
            this.areaLevels.fetch(), 
            this.reasons.fetch()).then(function() {
                _this.areaLevels.sort();
                loader.remove();
                _this.render();
            });
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'click #remove-actor-button': 'showRemoveModal',
        'click #add-actor-button': 'addActorEvent',
        'change #included-filter-select': 'changeFilter',
        'change select[name="activity-filter"]': 'renderActors'
    },

    /*
    * render the view
    */
    render: function(){
        var _this = this;
        var html = document.getElementById(this.template).innerHTML
        var template = _.template(html);
        this.el.innerHTML = template({
            casestudy: this.caseStudy.get('properties').name,
            keyflow: this.model.get('name'),
            activities: this.activities
        });
        this.filterSelect = this.el.querySelector('#included-filter-select');
        this.datatable = $('#actors-table').DataTable();
        this.renderActors();
    },
    
    renderActors: function(){
        var _this = this;
        var activityId = this.el.querySelector('select[name="activity-filter"]').value;
        this.datatable.clear();
        this.actorRows = [];
        this.actors.fetch({ 
            data: { activity: activityId },
            success: function(){
                _this.actors.each(function(actor){_this.addActorRow(actor)}); // you have to define function instead of passing this.addActorRow, else scope is wrong
            }
        });
    },

    changeFilter: function(event){
        var _this = this;
        this.showAll = event.target.value == '0';
        if (!this.showAll){
            $.fn.dataTable.ext.search.push(
                function(settings, data, dataIndex) {
                    console.log($(_this.datatable.row(dataIndex).node()).attr('data-included'))
                    return $(_this.datatable.row(dataIndex).node()).attr('data-included') == 'true';
                  }
              );
        }
        else $.fn.dataTable.ext.search.pop();
        this.datatable.draw();
    },

    /* 
    * add given actor to table
    */
    addActorRow: function(actor){
        var _this = this;

        var activity = _this.activities.get(actor.get('activity'));
        var dataRow = this.datatable.row.add([actor.get('name'), activity.get('name')]).draw(),
            row = dataRow.node();
        row.setAttribute('data-included', actor.get('included'));
        this.actorRows.push(row);
        
        function selectRow(r){
            _.each(_this.actorRows, function(row){
                row.classList.remove('selected');
            });
            r.classList.add('selected');
        }
        
        function setIncluded(actor){
            var included = actor.get('included');
            if (!included){
                row.classList.add('dsbld');
                if (!_this.showAll)
                    row.style.display = "none";
            } else {
                row.classList.remove('dsbld')
                row.style.display = "table-row";
            }
            row.setAttribute('data-included', included);
        };
        setIncluded(actor);
        
        // open a view on the actor (showing attributes and locations)
        function showActor(actor){
            selectRow(row);
            actor.caseStudyId = _this.caseStudy.id;
            actor.keyflowId = _this.model.id;
            _this.activeActor = actor;
            if (_this.actorView != null) _this.actorView.close();
            actor.fetch({ success: function(){
                _this.actorView = new EditActorView({
                    el: document.getElementById('edit-actor'),
                    template: 'edit-actor-template',
                    model: actor,
                    activities: _this.activities,
                    keyflow: _this.model,
                    onUpload: function(a) { 
                        setIncluded(a); 
                        dataRow.data([actor.get('name'), activity.get('name')]);
                        showActor(a); 
                    },
                    focusarea: _this.caseStudy.get('properties').focusarea,
                    areaLevels: _this.areaLevels,
                    reasons: _this.reasons
                });
            }})
        }

        // row is clicked -> open view and remember that this actor is "active"
        row.style.cursor = 'pointer';
        row.addEventListener('click', function() {
            if (_this.activeActor != actor || actor.id == null){
                if (_this.actorView != null && _this.actorView.hasChanged()){
                    var message = gettext('Attributes of the actor have been changed but not uploaded. <br><br>Do you want to discard the changes?');
                    _this.confirm({ 
                        message: message,
                        onConfirm: function() { showActor(actor) }
                    })
                }
                else showActor(actor);
            }
        });

        return dataRow;
    },

    /* 
    * add row on button click
    */
    addActorEvent: function(event){
        var _this = this;
        var buttonId = event.currentTarget.id;
        var tableId;

        function onChange(name){
            var actor = new Actor({
                "BvDid": "-",
                "name": name || "-----",
                "consCode": "-",
                "year": null,
                "turnover": null,
                "employees": null,
                "BvDii": "-",
                "website": "www.website.org",
                "activity": _this.activities.first().id,
                'reason': null
                }, {"caseStudyId": _this.model.get('casestudy'), 'keyflowId': _this.model.id});
            actor.save({}, {success: function(){
                _this.actors.add(actor);
                var row = _this.addActorRow(actor);
                row.node().click();
            }});
        }
        this.getName({ 
            title: gettext('Add Actor'),
            onConfirm: onChange
        });
    },

    /* 
    * show modal for removal on button click
    */
    showRemoveModal: function(){
        if (this.activeActor == null) return;
        var message = gettext('Do you really want to delete the actor') + ' &#60;' + this.activeActor.get('name') + '&#62; ' + '?';
        this.confirm({ message: message, onConfirm: this.removeActor });
    },

    /* 
    * remove selected actor on button click in modal
    */
    removeActor: function(){
        var _this = this;
        this.activeActor.destroy({success: function(){
            _this.actorView.close();
            _this.activeActor = null;
            _this.datatable.row('.selected').remove().draw( false );
        }});
    }

});
return ActorsView;
}
);