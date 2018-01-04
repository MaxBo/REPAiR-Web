define(['backbone', 'app/models/actor', 'app/collections/activities', 
        'app/collections/actors', 'app/views/data-entry-edit-actor',
        'tablesorter-pager', 'app/loader'],

function(Backbone, Actor, Activities, Actors, EditActorView){
  var ActorsView = Backbone.View.extend({

    /*
      * view-constructor
      */
    initialize: function(options){
      _.bindAll(this, 'render');
      var _this = this;
      
      this.template = options.template;
      var keyflowId = this.model.id,
          caseStudyId = this.model.get('casestudy');
      
      this.activities = new Activities([], {caseStudyId: caseStudyId, keyflowId: keyflowId});
      this.actors = new Actors([], {caseStudyId: caseStudyId, keyflowId: keyflowId});
      this.showAll = true;
      this.caseStudy = options.caseStudy;
      this.caseStudyId = this.model.get('casestudy');
      this.onUpload = options.onUpload;
      
      this.actorRows = [];
      
      var loader = new Loader(document.getElementById('actors-edit'),
        {disable: true});
        
      this.projection = 'EPSG:4326'; 
        
      $.when(this.activities.fetch(), this.actors.fetch()).then(function() {
          loader.remove();
          _this.render();
      });
    },

    /*
      * dom events (managed by jquery)
      */
    events: {
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
      this.el.innerHTML = template({casestudy: this.caseStudy.get('name'),
                                    keyflow: this.model.get('name')});

      this.filterSelect = this.el.querySelector('#included-filter-select');
      this.table = this.el.querySelector('#actors-table');

      // render inFlows
      this.actors.each(function(actor){_this.addActorRow(actor)}); // you have to define function instead of passing this.addActorRow, else scope is wrong
      
      this.setupTable();
    },
    
    setupTable: function(){
    
      $(this.table).tablesorter({
        //widgets: ['zebra']
      });
      
      // ToDo: set tablesorter pager if table is empty (atm deactivated in this case, throws errors)
      if ($(this.table).find('tr').length > 1)
        $(this.table).tablesorterPager({container: $("#pager")});
      
      // workaround for a bug in tablesorter-pager by triggering
      // event that pager-selection changed to redraw number of visible rows
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

    addActorRow: function(actor){
      var _this = this;

      var row = this.table.getElementsByTagName('tbody')[0].insertRow(-1);
      this.actorRows.push(row);
      
      var nameCell = row.insertCell(-1);
      var activityCell = row.insertCell(-1);
      
      
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
      
      function showActor(actor){
        if (_this.actorView != null) _this.actorView.close();
        _this.actorView = new EditActorView({
          el: document.getElementById('edit-actor'),
          template: 'edit-actor-template',
          model: actor,
          activities: _this.activities,
          keyflow: _this.model,
          onUpload: function(a) { setRowValues(a); showActor(a); }
        });
      }
      
      
      row.style.cursor = 'pointer';
      row.addEventListener('click', function() {
        _.each(_this.actorRows, function(row){
          row.classList.remove('selected');
        });
        row.classList.add('selected');
        if (_this.activeActorId != actor.id || actor.id == null){
          _this.activeActorId = actor.id;
          showActor(actor);
        }
      });

      return row;
    },

    /* 
     * add row when button is clicked 
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