define(['backbone', 'app/models/actor', 'app/collections/geolocations', 
        'app/models/geolocation', 'app/collections/activities', 
        'app/collections/actors', 'app/visualizations/map', 
        'tablesorter-pager', 'app/loader'],

function(Backbone, Actor, Locations, Geolocation, Activities, Actors, Map){
  var EditActorsView = Backbone.View.extend({

    /*
      * view-constructor
      */
    initialize: function(options){
      _.bindAll(this, 'render');
      
      this.template = options.template;
      var keyflowId = this.model.id,
          caseStudyId = this.model.get('casestudy');
      
      this.activities = new Activities([], {caseStudyId: caseStudyId, keyflowId: keyflowId});
      this.actors = new Actors([], {caseStudyId: caseStudyId, keyflowId: keyflowId});
      this.showAll = true;
      this.caseStudy = options.caseStudy;
      this.caseStudyId = this.model.get('casestudy');
      this.onUpload = options.onUpload;
      
      this.pins = {
        blue: '/static/img/simpleicon-places/svg/map-marker-blue.svg',
        orange: '/static/img/simpleicon-places/svg/map-marker-orange.svg',
        red: '/static/img/simpleicon-places/svg/map-marker-red.svg',
        black: '/static/img/simpleicon-places/svg/map-marker-1.svg'
      }
      
      // TODO: get this from database or template
      this.reasons = {
        //0: "Included",
        1: "Outside Region, inside country",
        2: "Outside Region, inside EU",
        3: "Outside Region, outside EU",
        4: "Outside Material Scope",
        5: "Does Not Produce Waste"
      }

      var _this = this;
      
      this.adminLocations = new Locations([], {
        caseStudyId: caseStudyId, keyflowId: keyflowId, type: 'administrative'
      })
      
      this.opLocations = new Locations([], {
        caseStudyId: caseStudyId, keyflowId: keyflowId, type: 'operational'
      })

      var loader = new Loader(document.getElementById('actors-edit'),
        {disable: true});
        
      this.projection = 'EPSG:4326'; 
        
      $.when(this.adminLocations.fetch(), this.opLocations.fetch(), this.activities.fetch(),
             this.actors.fetch()).then(function() {
          loader.remove();
          _this.render();
      });
    },

    /*
      * dom events (managed by jquery)
      */
    events: {
      'click #add-actor-button': 'addActorEvent'
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
        //headers:{
          //0: {sorter: false},
          //1: {sorter: 'inputs'},
          //2: {sorter: 'select'},
          //3: {sorter: 'inputs'},
          //4: {sorter: 'inputs'},
          //5: {sorter: 'inputs'},
          //6: {sorter: 'inputs'},
          //7: {sorter: 'inputs'},
          //8: {sorter: 'inputs'},
          //9: {sorter: 'inputs'}
        //},
        ////widgets: ['zebra']
      })
      
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
      for (var i = 1, row; row = this.table.rows[i]; i++) {
        if (!this.showAll && !row.cells[0].getElementsByTagName("input")[0].checked)
          row.style.display = "none";
        else
          row.style.display = "table-row";
      }
    },

    addActorRow: function(actor){
      var _this = this;

      var row = this.table.getElementsByTagName('tbody')[0].insertRow(-1);
      
      var included = actor.get('included')

      if (!included){
        row.classList.add('dsbld');
        if (!this.showAll)
          row.style.display = "block";
      }
      row.insertCell(-1).innerHTML = actor.get('name');
      var activity = this.activities.get(actor.get('activity'));
      row.insertCell(-1).innerHTML = activity.get('name');
      
      row.style.cursor = 'pointer';
      row.addEventListener('click', function() {
        //_this.el.querySelector('#actor-name').innerHTML = actor.get('name');
        //var selected = _this.table.getElementsByClassName("selected");
        //_.each(selected, function(row){
          //row.classList.remove('selected');
        //});
        //row.classList.add('selected');
        //if (_this.activeActorId != actor.id || actor.id == null){
          //_this.activeActorId = actor.id;
          //_this.renderLocations(actor);
        //}
      });

      return row;
    },

    /* 
     * add row when button is clicked 
     */
    addActorEvent: function(event){
      var buttonId = event.currentTarget.id;
      var tableId;
      var actor = new Actor({}, {
        "BvDid": "",
        "name": "",
        "consCode": "",
        "year": 0,
        "turnover": 0,
        "employees": 0,
        "BvDii": "",
        "website": "",
        "activity": null,
        "caseStudyId": this.model.get('casestudy')
      });
      this.actors.add(actor);
      var row = this.addActorRow(actor);
      // let tablesorter know, that there is a new row
      $('table').trigger('addRows', [$(row)]);
      // workaround for going to last page by emulating click
      document.getElementById('goto-last-page').click();
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
  return EditActorsView;
}
);