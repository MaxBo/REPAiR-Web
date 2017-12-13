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
      _.bindAll(this, 'addMarker');
      
      this.template = options.template;
      var keyflowId = this.model.id,
          caseStudyId = this.model.get('casestudy');
      
      this.activities = new Activities([], {caseStudyId: caseStudyId, keyflowId: keyflowId});
      this.actors = new Actors([], {caseStudyId: caseStudyId, keyflowId: keyflowId});
      this.showAll = true;
      this.onUpload = options.onUpload;
      
      this.pins = {
        blue: '/static/img/simpleicon-places/svg/map-marker-blue.svg',
        orange: '/static/img/simpleicon-places/svg/map-marker-orange.svg',
        red: '/static/img/simpleicon-places/svg/map-marker-red.svg'
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
        
      $.when(this.adminLocations.fetch(), this.opLocations.fetch(),
             this.actors.fetch()).then(function() {
          loader.remove();
          _this.render();
      });
    },

    /*
      * dom events (managed by jquery)
      */
    events: {
      'click #add-actor-button': 'addActorEvent', 
      'change #included-filter-select': 'changeFilter',
      'click #upload-actors-button': 'uploadChanges'
    },

    /*
      * render the view
      */
    render: function(){
      var _this = this;

      var html = document.getElementById(this.template).innerHTML
      var template = _.template(html);
      this.el.innerHTML = template({casestudy: this.model.get('name')});

      this.filterSelect = this.el.querySelector('#included-filter-select');
      this.table = this.el.querySelector('#actors-table');
      this.adminTable = this.el.querySelector('#adminloc-table').getElementsByTagName('tbody')[0];
      this.opTable = this.el.querySelector('#oploc-table').getElementsByTagName('tbody')[0];

      //// render inFlows
      this.actors.each(function(actor){_this.addActorRow(actor)}); // you have to define function instead of passing this.addActorRow, else scope is wrong
      
      this.setupTable();
      this.initMap();
    },
    
    setupTable: function(){
    
      // ToDo: modularize this 
      $.tablesorter.addParser({
          id: 'inputs',
          is: function(s) {
              return false;
          },
          format: function(s, table, cell, cellIndex) {
              var $c = $(cell);
              // return 1 for true, 2 for false, so true sorts before false
              if (!$c.hasClass('updateInput')) {
                  $c
                  .addClass('updateInput')
                  .bind('keyup', function() {
                      $(table).trigger('updateCell', [cell, false]); // false to prevent resort
                  });
              }
              return $c.find('input').val();
          },
          type: 'text'
      });
      $.tablesorter.addParser({
          id: 'select',
          is: function(s) {
              return false;
          },
          format: function(s, table, cell, cellIndex) {
              var $c = $(cell);
              // return 1 for true, 2 for false, so true sorts before false
              if (!$c.hasClass('updateInput')) {
                  $c
                  .addClass('updateInput')
                  .bind('keyup', function() {
                      $(table).trigger('updateCell', [cell, false]); // false to prevent resort
                  });
              }
              return $c.find('select option:selected').text();
          },
          type: 'text'
      });
      $(this.table).tablesorter({
        headers:{
          0: {sorter: false},
          1: {sorter: 'inputs'},
          2: {sorter: 'select'},
          3: {sorter: 'inputs'},
          4: {sorter: 'inputs'},
          5: {sorter: 'inputs'},
          6: {sorter: 'inputs'},
          7: {sorter: 'inputs'},
          8: {sorter: 'inputs'},
          9: {sorter: 'inputs'}
        },
        //widgets: ['zebra']
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
      //var row = document.createElement("TR");
      // checkbox for marking deletion

      var checkbox = document.createElement("input");
      checkbox.type = 'checkbox';
      var included = actor.get('included')
      checkbox.checked = included;
      if (!included){
        row.classList.add('dsbld');
        if (!this.showAll)
          row.style.display = "block";
      }
      row.insertCell(-1).appendChild(checkbox);

      checkbox.addEventListener('change', function() {
        row.classList.toggle('dsbld');
        actor.set('included', checkbox.checked);
      });

      var addInput = function(attribute, inputType){
        var input = document.createElement("input");
        if (inputType == 'number')
          input.type = 'number'
        input.value = actor.get(attribute);
        row.insertCell(-1).appendChild(input);

        input.addEventListener('change', function() {
          actor.set(attribute, input.value);
          input.classList.add('changed');
        });
      };

      addInput('name');

        // select input for activity

      var activitySelect = document.createElement("select");
      var ids = [];
      var targetId = actor.get('activity');
      this.activities.each(function(activity){
        var option = document.createElement("option");
        option.text = activity.get('name');
        option.value = activity.id;
        activitySelect.add(option);
        ids.push(activity.id);
      });
      var idx = ids.indexOf(targetId);
      activitySelect.selectedIndex = idx.toString();
      row.insertCell(-1).appendChild(activitySelect);

      activitySelect.addEventListener('change', function() {
        actor.set('activity', activitySelect.value);
        activitySelect.classList.add('changed');
      });

      addInput('website');
      addInput('year', 'number');
      addInput('turnover', 'number');
      addInput('employees', 'number');
      addInput('BvDid');
      addInput('BvDii');
      addInput('consCode');
      
      // row is clicked -> highlight and render locations on map      
      row.addEventListener('click', function() {
        _this.el.querySelector('#actor-name').innerHTML = actor.get('name');
        var selected = _this.table.getElementsByClassName("selected");
        _.each(selected, function(row){
          row.classList.remove('selected');
        });
        row.classList.add('selected');
        if (_this.activeActorId != actor.id || actor.id == null){
          _this.activeActorId = actor.id;
          _this.renderMarkers(actor);
        }
      });
      return row;
    },

    // add row when button is clicked
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

    uploadChanges: function(){

      var _this = this;

      var modelsToSave = [];

      var update = function(model){
        if (model.changedAttributes() != false && Object.keys(model.attributes).length > 0){
          modelsToSave.push(model);
        }
      };
      this.actors.each(update);
      //this.adminLocations.each(update);

      // chain save and destroy operations
      var saveComplete = _.invoke(modelsToSave, 'save');

      var loader = new Loader(document.getElementById('flows-edit'),
        {disable: true});
      var onError = function(response){
        alert(response.responseText); 
        loader.remove();
      };
      $.when.apply($, saveComplete).done(function(){
        loader.remove();
        console.log('upload complete');
        _this.onUpload();
      }).fail(onError);
    },
    
    initMap: function(){
      var _this = this;
      
      this.map = new Map({
        divid: 'actors-map', 
      });
      
      var onAddAdminLoc = function(obj){
        if (_this.activeActorId == null) return; 
        var adminLoc = _this.adminLocations.filterActor(_this.activeActorId)[0];
        if (adminLoc != null) return;
        var coord = _this.map.toProjection(obj.coordinate, _this.projection);
        _this.addLocation(coord, _this.adminLocations, _this.pins.blue, _this.adminTable);
      };
    
    
      var onAddOpLoc = function(obj){
        if (_this.activeActorId == null) return; 
        var coord = _this.map.toProjection(obj.coordinate, _this.projection);
        _this.addLocation(coord, _this.opLocations, _this.pins.red, _this.opTable);
      };
    
      var items = [
        {
          text: 'Add/Move Administr. Loc.',
          icon: this.pins.blue,
          callback: onAddAdminLoc
        },
        {
          text: 'Add Operational Loc.',
          icon: this.pins.red,
          callback: onAddOpLoc
        },
        '-' // this is a separator
      ];
      
      this.map.addContextMenu(items)
    },
    
    addLocation: function(coord, actors, pin, table){
      var properties = {actor: this.activeActorId}
      var loc = new actors.model({}, {caseStudyId: this.model.get('casestudy'),
                                      type: actors.type,
                                      properties: properties})
      loc.setGeometry(coord);
      actors.add(loc);
      this.addMarker(loc, pin, table);
    },
    
    
    addMarker: function(loc, pin, table){ 
      if (loc == null)
        return;
      function formatCoords(c){
        return c[0].toFixed(2) + ', ' + c[1].toFixed(2);
      }
      /* add table rows */
      
      var row = table.insertRow(-1);
      var _this = this;
      // add a crosshair icon to center on coordinate on click
      var centerDiv = document.createElement('div');
      //centerDiv.className = "fa fa-crosshairs";
      var img = document.createElement("img");
      img.src = pin;
      img.setAttribute('height', '30px');
      centerDiv.appendChild(img);
      var cell = row.insertCell(-1);
      var coords = loc.get('geometry').get('coordinates');
      cell.appendChild(centerDiv);
      cell.addEventListener('click', function(){ 
        _this.map.center(coords, {projection: _this.projection})
      });
      cell.style.cursor = 'pointer';
      var coordCell = row.insertCell(-1);
      coordCell.innerHTML = formatCoords(coords);
      row.insertCell(-1).innerHTML = loc.get('properties').note;
      
      /* add markers */
      
      this.map.addmarker(coords, { 
        icon: pin, 
        //dragIcon: this.pins.orange, 
        projection: this.projection,
        onDrag: function(coords){
          coordCell.innerHTML = formatCoords(coords);
          loc.get('geometry').set("coordinates", coords);
        }
      });
    },
    
    renderMarkers: function(actor){
      
      var adminLoc = this.adminLocations.filterActor(actor.id)[0];
          opLocList = this.opLocations.filterActor(actor.id);
      
      var _this = this;
      this.adminTable.innerHTML = '';
      this.opTable.innerHTML = '';
      
      this.map.removeMarkers();
      this.addMarker(adminLoc, this.pins.blue, this.adminTable);
      _.each(opLocList, function(loc){_this.addMarker(loc, _this.pins.red, _this.opTable);});
      
      if (adminLoc != null)
        this.map.center(adminLoc.get('geometry').get('coordinates'),
                        {projection: this.projection});
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