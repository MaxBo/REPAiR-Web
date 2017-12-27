define(['backbone', 'app/models/actor', 'app/collections/geolocations', 
        'app/models/geolocation', 'app/collections/activities', 
        'app/collections/actors', 'app/visualizations/map', 
        'tablesorter-pager', 'app/loader'],

function(Backbone, Actor, Locations, Geolocation, Activities, Actors, Map){
  if (typeof jQuery.when.all === 'undefined') {
      jQuery.when.all = function (deferreds) {
          return $.Deferred(function (def) {
              $.when.apply(jQuery, deferreds).then(
                  function () {
                      def.resolveWith(this, [Array.prototype.slice.call(arguments)]);
                  },
                  function () {
                      def.rejectWith(this, [Array.prototype.slice.call(arguments)]);
                  });
          });
      }
  }
  function formatCoords(c){
    return c[0].toFixed(2) + ', ' + c[1].toFixed(2);
  }
  var EditActorsView = Backbone.View.extend({

    /*
      * view-constructor
      */
    initialize: function(options){
      _.bindAll(this, 'render');
      _.bindAll(this, 'renderLocation');
      
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
      'click #add-actor-button': 'addActorEvent', 
      'change #included-filter-select': 'changeFilter',
      'click #upload-actors-button': 'uploadChanges',
      'click #confirm-location': 'locationConfirmed',
      'click #add-operational-button,  #add-administrative-button': 'createLocationEvent'
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
      
      /* column INCLUDED with reason of exclusion*/

      var inclusionWrapper = document.createElement("div");
      inclusionWrapper.style = 'min-width: 200px;';
      var checkbox = document.createElement("input");
      checkbox.type = 'checkbox';
      var included = actor.get('included')
      checkbox.checked = included;
      inclusionWrapper.appendChild(checkbox);
      
      var form = document.createElement("form");
      var radios = [];
      var targetReason = actor.get('reason');
      
      // add radio button with reason
      function addRadio(reasonId, name){
        var span = document.createElement("span");
        span.style = 'white-space: nowrap;';
        var radio = document.createElement("input");
        radio.type = 'radio';
        radio.style = 'margin-right: 2px;';
        radio.name = 'actor' + actor.id;
        radio.value = reasonId;
        span.appendChild(radio);
        form.appendChild(span);
        form.appendChild(document.createElement("br"));
        radios.push(radio);
        // set reason to model on change by user
        radio.addEventListener('change', function() {
          actor.set('reason', radio.value);
        });
        // set reason as stored in model
        if (reasonId == targetReason){
          radio.checked = true;
        }
        var label = document.createElement("label");
        label.innerHTML = name;
        span.appendChild(label);
      }
      // iterate reasons and add radio buttons for each one
      for (var reasonId in this.reasons){
        addRadio(reasonId, this.reasons[reasonId]);
      };
      inclusionWrapper.appendChild(form);
      
      row.insertCell(-1).appendChild(inclusionWrapper);

      if (!included){
        row.classList.add('dsbld');
        if (!this.showAll)
          row.style.display = "block";
      }
      else
        form.style.display = "none";
      
      // set inclusion/exclusion made by user to model, show/hide reason
      checkbox.addEventListener('change', function() {
        row.classList.toggle('dsbld');
        actor.set('included', checkbox.checked);
        if(checkbox.checked){
          form.style.display = "none";
          // set reason to "included"
          actor.set('reason', 0);
        }
        else {
          form.style.display = "block";
          // reason 0 is "included" - set it to first other reason available
          if (actor.get('reason') == 0){
            actor.set('reason', 1)
            radios[0].checked = true; // radios-array starts with first reason other than "included"
          }
        }
      });
      
      /* add an input-field to the row, 
       * tracking changes made by user to the attribute and automatically updating the model 
       */
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

     
      /* column ACTIVITY (selection)*/

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

      
      /* other simple input-columns*/
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
          _this.renderLocations(actor);
        }
      });
      return row;
    },

    /* 
     * add row when button is clicked 
     */
    addActorEvent: function(event){
      var buttonId = event.currentTarget.id;
      var tableId;
      var actor = new Actor({
        "BvDid": "",
        "name": "---------",
        "consCode": "",
        "year": 0,
        "turnover": 0,
        "employees": 0,
        "BvDii": "",
        "website": "",
        "activity": null,
        "included": true
         }, 
         {"caseStudyId": this.model.get('casestudy')}
      );
      this.actors.add(actor);
      var row = this.addActorRow(actor);
      // let tablesorter know, that there is a new row
      $('table').trigger('addRows', [$(row)]);
      // workaround for going to last page by emulating click
      document.getElementById('goto-last-page').click();
    },

    /* 
     * check the models for changes and upload the changed/added ones 
     */
    uploadChanges: function(){

      var _this = this;

      var deferreds = [],
          errors = {},
          success = {};

      var update = function(model){
        if (model.changedAttributes() != false && Object.keys(model.attributes).length > 0){
          deferreds.push(
            model.save({}, {
              success: function(model, response){console.log(model)},
              error: function(model, response){errors[model.id] = model.get('name') + ': ' + response.responseText}
            }));
        }
      };
      this.actors.each(update);
      
      var loader = new Loader(document.getElementById('flows-edit'),
        {disable: true});
        
      var onError = function(response){
        var errText = '';
        for (var modelId in errors)
          errText = errors[modelId] + '</br>';
        //console.log(response.getAllResponseHeaders())
        document.getElementById('alert-message').innerHTML = errText; 
        loader.remove();
        $('#alert-modal').modal('show'); 
      };
      
      $.when.apply($, deferreds).done(function(response){
        console.log(response)
        loader.remove();
        console.log('upload complete');
        _this.onUpload();
      }).fail(onError);
    },
    
    /* 
     * initial setup of the map-view
     */
    initMap: function(){
      var _this = this;
      
      this.map = new Map({
        divid: 'actors-map', 
      });
      
     this.localMap = new Map({
        divid: 'edit-location-map', 
      });
      
      // event triggered when modal dialog is ready -> trigger rerender to match size
      $('#location-modal').on('shown.bs.modal', function () {
        _this.localMap.map.updateSize();
     });
      //this.localMap.map.updateSize();
      //this.localMap.map.render();
      
      //var onAddAdminLoc = function(obj){
        //if (_this.activeActorId == null) return; 
        //var adminLoc = _this.adminLocations.filterActor(_this.activeActorId)[0];
        //if (adminLoc != null) return;
        //var coord = _this.map.toProjection(obj.coordinate, _this.projection);
        //_this.addLocation(coord, _this.adminLocations, _this.pins.blue, _this.adminTable);
      //};
    
    
      //var onAddOpLoc = function(obj){
        //if (_this.activeActorId == null) return; 
        //var coord = _this.map.toProjection(obj.coordinate, _this.projection);
        //_this.addLocation(coord, _this.opLocations, _this.pins.red, _this.opTable);
      //};
    
      //var items = [
        //{
          //text: 'Add/Move Administr. Loc.',
          //icon: this.pins.blue,
          //callback: onAddAdminLoc
        //},
        //{
          //text: 'Add Operational Loc.',
          //icon: this.pins.red,
          //callback: onAddOpLoc
        //},
        //'-' // this is a separator
      //];
      
      //this.map.addContextMenu(items)
    },
    
    
    /* 
     * add a marker with given location to the map and the table
     */
    renderLocation: function(loc, pin, table){ 
      if (loc == null)
        return;
      /* add table rows */
      
      var row = table.insertRow(-1);
      var _this = this;
      // add a crosshair icon to center on coordinate on click
      var centerDiv = document.createElement('div');
      var markerCell = row.insertCell(-1);
      var geom = loc.get('geometry');
      // add a marker to the table and the map, if there is a geometry attached to the location
      if (geom != null){
        //centerDiv.className = "fa fa-crosshairs";
        var img = document.createElement("img");
        img.src = pin;
        img.setAttribute('height', '30px');
        centerDiv.appendChild(img);
        var coords = geom.get('coordinates');
        markerCell.appendChild(centerDiv);
        // zoom to location if marker in table is clicked 
        markerCell.addEventListener('click', function(){ 
          _this.map.center(loc.get('geometry').get('coordinates'), 
                          {projection: _this.projection})
        });
        markerCell.style.cursor = 'pointer';
        
      /* add marker */
      
        this.map.addmarker(coords, { 
          icon: pin, 
          //dragIcon: this.pins.orange, 
          projection: this.projection,
          name: loc.get('properties').name,
          onDrag: function(coords){
            loc.get('geometry').set("coordinates", coords);
          }
        });
      };
      row.insertCell(-1).innerHTML = loc.get('properties').name;
      var editBtn = document.createElement('button');
      var pencil = document.createElement('span');
      editBtn.classList.add('btn');
      editBtn.classList.add('btn-primary');
      editBtn.classList.add('square');
      editBtn.style.float = 'right';
      editBtn.appendChild(pencil);
      pencil.classList.add('glyphicon');
      pencil.classList.add('glyphicon-pencil');
      
      editBtn.addEventListener('click', function(){
        _this.editLocation(loc);
      });
      
      row.insertCell(-1).appendChild(editBtn);
      
    },
    
    editLocation: function(location){
      var _this = this;
      this.editedLocation = location;
      var geometry = location.get('geometry');
      var markerId;
      var coordinates = (geometry != null) ? geometry.get("coordinates"): null;
      var type = location.type || location.collection.type;
      var pin = (type == 'administrative') ? this.pins.blue : this.pins.red
      var inner = document.getElementById('location-modal-template').innerHTML;
      var template = _.template(inner);
      var html = template({properties: location.get('properties'), 
                           coordinates: (coordinates != null)? formatCoords(coordinates): '-'});
      document.getElementById('location-modal-content').innerHTML = html;
      $('#location-modal').modal('show'); 
      this.localMap.removeMarkers();
      function addMarker(coords){
        markerId = _this.localMap.addmarker(coords, { 
          icon: pin, 
          //dragIcon: this.pins.orange, 
          projection: _this.projection,
          name: location.get('properties').name,
          onDrag: function(coords){
            geometry.set("coordinates", coords);
            elGeom.innerHTML = formatCoords(coords);
          },
          onRemove: function(){
            location.set('geometry', null);
            elGeom.innerHTML = '-';
          }
        });
        _this.localMap.center(coords, {projection: _this.projection});
      }
      if (coordinates != null){
        var elGeom = document.getElementById('coordinates');
        addMarker(coordinates)
      };

      var items = [
        {
          text: 'Set Location',
          icon: pin,
          callback: function(event){
            var coords = _this.localMap.toProjection(event.coordinate, _this.projection)
            if (geometry != null){
              _this.localMap.moveMarker(markerId, event.coordinate);
              geometry.set("coordinates", coords);
              elGeom.innerHTML = formatCoords(coords);
            }
            else{
              location.setGeometry(coords);
              addMarker(coords);
            }
          }
        },
        '-'
      ];
      
      this.localMap.addContextMenu(items);
      
    },
    
    createLocationEvent(event){
      var buttonId = event.currentTarget.id;
      var properties = {actor: this.activeActorId}
      var type = (buttonId == 'add-administrative-button') ? 'administrative': 'operational';
      var location = new Geolocation({properties: properties}, 
                                     {caseStudyId: this.model.get('casestudy'),
                                      type: type});
      this.editLocation(location);
    },
    
    
    locationConfirmed: function(){
      var location = this.editedLocation;
      if(location == null) return;
      var table = document.getElementById('location-edit-table');
      var inputs = table.querySelectorAll('input');
      var properties = location.get('properties');
      _.each(inputs, function(input){
        //properties.set(input.name) = input.value;
        properties[input.name] = input.value;
      });
      // location is not in a collection (added by clicking add-button) -> add it to the proper one
      if (location.collection == null){
        var collection = (location.type == 'administrative') ? this.adminLocations : this.opLocations;
        collection.add(location);
      }
      // rerender actor and markers
      var actor = this.actors.get(this.activeActorId);
      this.renderLocations(actor);
    },
    
    /* 
     * render the locations of the given actor as markers inside the map and table
     */
    renderLocations: function(actor){
      document.getElementById('location-wrapper').style.display = 'block';
      var adminLoc = this.adminLocations.filterActor(actor.id)[0];
          opLocList = this.opLocations.filterActor(actor.id);
      
      var _this = this;
      this.adminTable.innerHTML = '';
      this.opTable.innerHTML = '';
      
      this.map.removeMarkers();
      this.renderLocation(adminLoc, this.pins.blue, this.adminTable);
      _.each(opLocList, function(loc){_this.renderLocation(loc, _this.pins.red, _this.opTable);});
      
      var addAdminBtn = document.getElementById('add-administrative-button');
      if (adminLoc != null){
        // you may not have more than one admin. location (hide button, if there already is one)
        addAdminBtn.style.display = 'none';
        this.map.center(adminLoc.get('geometry').get('coordinates'),
                        {projection: this.projection});
      }
      else addAdminBtn.style.display = 'block';
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