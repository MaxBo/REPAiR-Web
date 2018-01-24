define(['backbone', 'underscore', 'models/actor', 'collections/activities',
        'collections/actors', 'collections/arealevels', 'views/data-entry-edit-actor',
        'loader', 'app-config', 'tablesorter'],
function(Backbone, _, Actor, Activities, Actors, AreaLevels, EditActorView, 
         Loader, config){
  /**
   *
   * @author Christoph Franke
   * @name module:views/ActorsView
   * @augments Backbone.View
   */
  var ActorsView = Backbone.View.extend(
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
      var _this = this;
      
      this.template = options.template;
      var keyflowId = this.model.id,
          caseStudyId = this.model.get('casestudy');
      
      this.activities = new Activities([], { caseStudyId: caseStudyId, keyflowId: keyflowId });
      this.actors = new Actors([], { caseStudyId: caseStudyId, keyflowId: keyflowId });
      this.areaLevels = new AreaLevels([], { caseStudyId: caseStudyId })
      this.showAll = true;
      this.caseStudy = options.caseStudy;
      this.caseStudyId = this.model.get('casestudy');
      
      this.actorRows = [];
      
      var loader = new Loader(document.getElementById('actors-edit'),
        {disable: true});
        
      this.projection = 'EPSG:4326'; 
      
      var Reasons = Backbone.Collection.extend({url: config.api.reasons});
      this.reasons = new Reasons([]);
        
      $.when(this.activities.fetch(), this.actors.fetch(), 
             this.areaLevels.fetch(), this.reasons.fetch()).then(function() {
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
      'click #confirm-button': 'removeActorEvent',
      'click #add-actor-button': 'addActorEvent',
      'change #included-filter-select': 'changeFilter'
    },

    /*
     * render the view
     */
    render: function(){
      var _this = this;
      var html = document.getElementById(this.template).innerHTML
      var template = _.template(html);
      this.el.innerHTML = template({casestudy: this.caseStudy.get('properties').name,
                                    keyflow: this.model.get('name')});
      
      // confirmation modal for deletion of actor
      html = document.getElementById('confirmation-template').innerHTML
      template = _.template(html);
      this.elConfirmation = document.getElementById('confirmation-modal');
      this.elConfirmation.innerHTML = template({message: ''});

      this.filterSelect = this.el.querySelector('#included-filter-select');
      this.table = this.el.querySelector('#actors-table');

      // render inFlows
      this.actors.each(function(actor){_this.addActorRow(actor)}); // you have to define function instead of passing this.addActorRow, else scope is wrong
      
      this.setupTable();
    },
    
    /* 
     * set up the actors table (tablesorter)
     */
    setupTable: function(){
      require('libs/jquery.tablesorter.pager');
      $(this.table).tablesorter({
        widgets: ['filter'], //, 'zebra']
        widgetOptions : {
          filter_placeholder: { search : gettext('Search') + '...' }
        }
      });
      // ToDo: set tablesorter pager if table is empty (atm deactivated in this case, throws errors)
      if ($(this.table).find('tr').length > 1)
        $(this.table).tablesorterPager({container: $("#pager")});
      
      //workaround for a bug in tablesorter-pager by triggering
      //event that pager-selection changed to redraw number of visible rows
      var sel = document.getElementById('pagesize');
      sel.selectedIndex = 0;
      sel.dispatchEvent(new Event('change'));
    },

    changeFilter: function(event){
      this.showAll = event.target.value == '0';
      for (var i = 1, row; row = this.actorRows[i]; i++) {
        if (!this.showAll && row.classList.contains('dsbld'))
          row.style.display = "none";
        else
          row.style.display = "table-row";
      }
    },

    /* 
     * add given actor to table
     */
    addActorRow: function(actor){
      var _this = this;

      var row = this.table.getElementsByTagName('tbody')[0].insertRow(-1);
      this.actorRows.push(row);
      
      var nameCell = row.insertCell(-1);
      var activityCell = row.insertCell(-1);
      
      // fill the row with the attributes of the actor and change it's style depending on status of actor
      function setRowValues(actor){
        var included = actor.get('included');
        if (!included){
          row.classList.add('dsbld');
          if (!_this.showAll)
            row.style.display = "none";
        } else {
          row.classList.remove('dsbld')
          row.style.display = "table-row";
        }
        
        nameCell.innerHTML = actor.get('name');
        var activity = _this.activities.get(actor.get('activity'));
        activityCell.innerHTML = (activity != null)? activity.get('name'): '-';
      };
      setRowValues(actor);
      
      // open a view on the actor (showing attributes and locations)
      function showActor(actor){
        if (_this.actorView != null) _this.actorView.close();
        _this.actorView = new EditActorView({
          el: document.getElementById('edit-actor'),
          template: 'edit-actor-template',
          model: actor,
          activities: _this.activities,
          keyflow: _this.model,
          onUpload: function(a) { setRowValues(a); showActor(a); },
          focusarea: _this.caseStudy.get('properties').focusarea,
          areaLevels: _this.areaLevels,
          reasons: _this.reasons
        });
      }
      
      // row is clicked -> open view and remember that this actor is "active"
      row.style.cursor = 'pointer';
      row.addEventListener('click', function() {
        _.each(_this.actorRows, function(row){
          row.classList.remove('selected');
        });
        row.classList.add('selected');
        if (_this.activeActor != actor || actor.id == null){
          _this.activeActor = actor;
          _this.activeRow = row;
          showActor(actor);
        }
      });

      return row;
    },

    /* 
     * add row on button click
     */
    addActorEvent: function(event){
      var _this = this;
      var buttonId = event.currentTarget.id;
      var tableId;
      var actor = new Actor({
        "BvDid": "-",
        "name": "-----",
        "consCode": "-",
        "year": 0,
        "turnover": 0,
        "employees": 0,
        "BvDii": "-",
        "website": "www.website.org",
        "activity": this.activities.first().id,
        }, {"caseStudyId": this.model.get('casestudy')});
      actor.save({}, {success: function(){
        _this.actors.add(actor);
        var row = _this.addActorRow(actor);
        // let tablesorter know, that there is a new row
        $('table').trigger('addRows', [$(row)]);
        // workaround for going to last page by emulating click (thats where new row is added)
        document.getElementById('goto-last-page').click();
        // click row to show details of new actor in edit view
        row.click();
      }});
    },
    
    /* 
     * show modal for removal on button click
     */
    showRemoveModal: function(){
      if (this.activeActor == null) return;
      var modal = this.elConfirmation.querySelector('.modal');
      // ToDo: translation
      var message = gettext('Do you really want to delete the actor') + ' &#60;' + this.activeActor.get('name') + '&#62; ' + '?';
      document.getElementById('confirmation-message').innerHTML = message; 
      $(modal).modal('show'); 
    },
    
    /* 
     * remove selected actor on button click in modal
     */
    removeActorEvent: function(){
      var _this = this;
      this.activeActor.destroy({success: function(){
        _this.actorView.close();
        _this.activeRow.style.display = 'none';
        //_this.activeRow.parentNode.removeChild(_this.activeRow);
        //document.getElementById('goto-first-page').click();
        //$(_this.table).trigger('update');
        //$(_this.table).trigger("appendCache");
        _this.activeActor = null;
        _this.activeRow = null;
      }});
    },
        
    /**
     * remove this view from the DOM
     */
    close: function(){
      this.undelegateEvents(); // remove click events
      this.unbind(); // Unbind all local event bindings
      this.el.innerHTML = ''; //empty the DOM element
    },

  });
  return ActorsView;
}
);