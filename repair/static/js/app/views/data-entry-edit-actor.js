define(['backbone', 'app/models/actor', 'app/collections/geolocations', 
        'app/models/geolocation', 'app/collections/activities', 
        'app/collections/actors', 'app/visualizations/map', 
        'tablesorter-pager', 'app/loader'],

function(Backbone, Actor, Locations, Geolocation, Activities, Actors, Map){
  function formatCoords(c){
    return c[0].toFixed(2) + ', ' + c[1].toFixed(2);
  }
  /**
   *
   * @author Christoph Franke
   * @name module:views/EditActorView
   * @augments Backbone.View
   */
  var EditActorView = Backbone.View.extend(
    /** @lends module:views/EditActorView.prototype */
    {

    /**
     * callback for uploading the actor
     *
     * @callback module:views/EditActorView~onUpload
     * @param {module:models/Actor} actor the uploaded actor
     */
     
    /**
     * render view to edit single actor and its locations
     *
     * @param {Object} options
     * @param {HTMLElement} options.el                                 element the view will be rendered in
     * @param {string} options.template                                id of the script element containing the underscore template to render this view
     * @param {module:models/Actor} options.model                      the actor to edit
     * @param {module:collections/Keyflows.Model} options.keyflow      the keyflow the actor belongs to
     * @param {Backbone.Collection} options.activities                 the activities belonging to the keyflow
     * @param {module:views/EditActorView~onUpload=} options.onUpload  called after successfully uploading the actor
     *
     * @constructs
     * @see http://backbonejs.org/#View
     */
    initialize: function(options){
      _.bindAll(this, 'render');
      _.bindAll(this, 'renderLocation');
      
      this.template = options.template;
      this.keyflow = options.keyflow;
      var keyflowId = this.keyflow.id,
          caseStudyId = this.keyflow.get('casestudy');
      
      this.activities = options.activities;
      this.onUpload = options.onUpload;
      
      this.pins = {
        blue: '/static/img/simpleicon-places/svg/map-marker-blue.svg',
        orange: '/static/img/simpleicon-places/svg/map-marker-orange.svg',
        red: '/static/img/simpleicon-places/svg/map-marker-red.svg',
        black: '/static/img/simpleicon-places/svg/map-marker-1.svg'
      }
      
      // TODO: get this from database or template
      this.reasons = [
        //0: "Included",
        {id: 1, name: "Outside Region, inside country"},
        {id: 2, name: "Outside Region, inside EU"},
        {id: 3, name: "Outside Region, outside EU"},
        {id: 4, name: "Outside Material Scope"},
        {id: 5, name: "Does Not Produce Waste"}
      ]

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
        
      $.when(this.adminLocations.fetch({ data: { actor: this.model.id } }), 
             this.opLocations.fetch({ data: { actor: this.model.id } })).then(function() {
          loader.remove();
          _this.render();
      });
    },

    /*
     * dom events (managed by jquery)
     */
    events: {
      'click #upload-actor-button': 'uploadChanges',
      'click #confirm-location': 'locationConfirmed',
      'click #add-operational-button,  #add-administrative-button': 'createLocationEvent',
      'change #included-check': 'toggleIncluded'
    },

    /*
      * render the view
      */
    render: function(){
      var _this = this;
      var html = document.getElementById(this.template).innerHTML
      var template = _.template(html);
      this.el.innerHTML = template({activities: this.activities,
                                    actor: this.model,
                                    reasons: this.reasons});

      this.filterSelect = this.el.querySelector('#included-filter-select');
      this.table = this.el.querySelector('#actors-table');
      this.adminTable = this.el.querySelector('#adminloc-table').getElementsByTagName('tbody')[0];
      this.opTable = this.el.querySelector('#oploc-table').getElementsByTagName('tbody')[0];

      this.initMap();
      this.renderLocations();
    },


    /* 
     * check the models for changes and upload the changed/added ones 
     */
    uploadChanges: function(){
      var actor = this.model;
      var _this = this;
      
      var table = document.getElementById('actor-edit-table');
      var inputs = Array.prototype.slice.call(table.querySelectorAll('input'));
      var selects = Array.prototype.slice.call(table.querySelectorAll('select'));
      _.each(inputs.concat(selects), function(input){
        if (input.name == 'reason' || input.name == 'included') return; // continue, handled seperately (btw 'return' in _.each(...) is equivalent to continue)
        actor.set(input.name, input.value);
      });
      var included = this.el.querySelector('input[name = "included"]').checked;
      actor.set('included', included);
      var checked = this.el.querySelector('input[name = "reason"]:checked')
      var reason = (checked != null) ? checked.value: this.reasons[0].id;
      actor.set('reason', reason);
      
      var loader = new Loader(this.el, {disable: true});
      
      var onError = function(response){
        document.getElementById('alert-message').innerHTML = response.responseText; 
        loader.remove();
        $('#alert-modal').modal('show'); 
      };
      
      //actor.save(null, {success: uploadLocations, error: function(model, response){onError(response)}});
      var models = [];
      models.push(actor);
      if (this.adminLocations.length > 0)
        models.push(this.adminLocations.first());
      this.opLocations.each(function(model){models.push(model)});
      function uploadModel(models, it){
        // end recursion if no elements are left and call the passed success method
        if (it >= models.length) {
          loader.remove();
          _this.onUpload(actor);
          return;
        };
        var model = models[it];
        // upload or destroy current model and upload next model recursively on success
        var params = {
            success: function(){ uploadModel(models, it+1) },
            error: function(model, response){ onError(response) }
          }
        if (model.markedForDeletion)
          model.destroy(params);
        else {
          var geom = model.get('geometry');
          // workaround: backend doesn't except empty geometries but null as a geometry
          if (geom != null && geom.get('coordinates') == null) model.set('geometry', null);
          model.save(null, params);
        }
      };
      
      // recursively queue the operational locations to save only when previous one is done (sqlite is bitchy with concurrent uploads)
      uploadModel(models, 0);
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
    },
    
    /* 
     * add a location to the map
     */
    addLocation: function(coord, locations, pin, table){
      var properties = {actor: this.activeActorId}
      var loc = new locations.model({}, {caseStudyId: this.model.get('casestudy'),
                                          type: locations.loc_type,
                                          properties: properties})
      loc.setGeometry(coord);
      locations.add(loc);
      this.renderLocation(loc, pin, table);
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
      
      // add an icon to center on coordinate on click
      
      var markerCell = row.insertCell(-1);
      var geom = loc.get('geometry');
      // add a marker to the table and the map, if there is a geometry attached to the location
      if (geom != null && geom.get('coordinates') != null){
        var wrapper = document.createElement('span'),
            centerDiv = document.createElement('div'),
            coordDiv = document.createElement('div'),
            img = document.createElement("img");
        var coords = geom.get('coordinates');
        coordDiv.innerHTML = '(' + formatCoords(coords) + ')';
        coordDiv.style.paddingTop = '5px';
        coordDiv.style.fontSize = '80%';
        img.src = pin;
        img.setAttribute('height', '30px');
        img.style.float = 'left';
        centerDiv.appendChild(img);
        markerCell.appendChild(wrapper);
        wrapper.style.whiteSpace = 'nowrap';
        wrapper.style.cursor = 'pointer';
        wrapper.appendChild(centerDiv);
        wrapper.appendChild(coordDiv);
        
        // zoom to location if marker in table is clicked 
        markerCell.addEventListener('click', function(){ 
          _this.map.center(loc.get('geometry').get('coordinates'), 
                          {projection: _this.projection})
        });
        
      /* add marker */
      
        this.map.addmarker(coords, { 
          icon: pin, 
          //dragIcon: this.pins.orange, 
          projection: this.projection,
          name: loc.get('properties').name,
          onDrag: function(coords){
            loc.get('geometry').set("coordinates", coords);
            coordDiv.innerHTML = '(' + formatCoords(coords) + ')';
          }
        });
      };
      
      // checkbox for marking deletion

      var checkbox = document.createElement("input");
      checkbox.type = 'checkbox';
      row.insertCell(-1).appendChild(checkbox);

      checkbox.addEventListener('change', function() {
        row.classList.toggle('strikeout');
        row.classList.toggle('dsbld');
        loc.markedForDeletion = checkbox.checked;
      });
      
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
    
    createLocationEvent(event){
      var buttonId = event.currentTarget.id;
      var properties = {actor: this.model.id}
      var type = (buttonId == 'add-administrative-button') ? 'administrative': 'operational';
      var location = new Geolocation({properties: properties}, 
                                     {caseStudyId: this.keyflow.get('casestudy'),
                                      type: type});
      this.editLocation(location);
    },
    
    editLocation: function(location){
      var _this = this;
      this.editedLocation = location;
      var geometry = location.get('geometry');
      var markerId;
      var coordinates = (geometry != null) ? geometry.get("coordinates"): null;
      var type = location.loc_type || location.collection.loc_type;
      var pin = (type == 'administrative') ? this.pins.blue : this.pins.red
      var inner = document.getElementById('location-modal-template').innerHTML;
      var template = _.template(inner);
      var html = template({properties: location.get('properties'), 
                           coordinates: (coordinates != null)? formatCoords(coordinates): '-'});
      document.getElementById('location-modal-content').innerHTML = html;
      $('#location-modal').modal('show'); 
      this.localMap.removeMarkers();
      // don't set coordinates directly to location, only on confirmation
      this.tempCoords = coordinates;
      function addMarker(coords){
        markerId = _this.localMap.addmarker(coords, { 
          icon: pin, 
          //dragIcon: this.pins.orange, 
          projection: _this.projection,
          name: location.get('properties').name,
          onDrag: function(coords){
            _this.tempCoords = coords;
            elGeom.innerHTML = formatCoords(coords);
          },
          onRemove: function(){
            _this.tempCoords = null;
            elGeom.innerHTML = '-';
          }
        });
        _this.localMap.center(coords, {projection: _this.projection});
      }
      if (coordinates != null){
        var elGeom = document.getElementById('coordinates');
        elGeom.innerHTML = formatCoords(coordinates);
        addMarker(coordinates);
      };

      var items = [
        {
          text: 'Set Location',
          icon: pin,
          callback: function(event){
            var coords = _this.localMap.toProjection(event.coordinate, _this.projection);
            _this.tempCoords = coords;
            if (geometry != null && geometry.get('coordinates') != null){
              _this.localMap.moveMarker(markerId, event.coordinate);
              elGeom.innerHTML = formatCoords(coords);
            }
            else{
              addMarker(coords);
            }
          }
        },
        '-'
      ];
      
      this.localMap.addContextMenu(items);
      
    },
    
    locationConfirmed: function(){
      var location = this.editedLocation;
      if(location == null) return;
      
      var geometry = location.get('geometry');
      if (geometry != null) geometry.set("coordinates", this.tempCoords);
      else location.setGeometry(this.tempCoords)
      var table = document.getElementById('location-edit-table');
      var inputs = table.querySelectorAll('input');
      var properties = location.get('properties');
      _.each(inputs, function(input){
        //properties.set(input.name) = input.value;
        properties[input.name] = input.value;
      });
      // location is not in a collection yet (added by clicking add-button) -> add it to the proper one
      if (location.collection == null){
        var collection = (location.loc_type == 'administrative') ? this.adminLocations : this.opLocations;
        collection.add(location);
      }
      // rerender all markers (too lazy to add single one)
      this.renderLocations();
    },
    
    /* 
     * render the locations of the given actor as markers inside the map and table
     */
    renderLocations: function(){
      var adminLoc = this.adminLocations.first();
      
      var _this = this;
      this.adminTable.innerHTML = '';
      this.opTable.innerHTML = '';
      
      this.map.removeMarkers();
      this.renderLocation(adminLoc, this.pins.blue, this.adminTable);
      this.opLocations.each(function(loc){_this.renderLocation(loc, _this.pins.red, _this.opTable);});
      
      var addAdminBtn = document.getElementById('add-administrative-button');
      if (adminLoc != null){
        // you may not have more than one admin. location (hide button, if there already is one)
        addAdminBtn.style.display = 'none';
        var geom = adminLoc.get('geometry');
        if (geom != null && geom.get('coordinates') != null)
          this.map.center(adminLoc.get('geometry').get('coordinates'),
                          {projection: this.projection});
      }
      else addAdminBtn.style.display = 'block';
    },
    
    toggleIncluded(event){
      var display = (event.target.checked) ? 'none': 'block';
      document.getElementById('reasons').style.display = display;
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
  return EditActorView;
}
);