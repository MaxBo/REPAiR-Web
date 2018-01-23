define(['backbone', 'underscore', 'models/actor', 'collections/geolocations', 
        'models/geolocation', 'collections/activities', 'collections/actors', 
        'collections/areas', 'models/area','visualizations/map', 'loader'],

function(Backbone, _, Actor, Locations, Geolocation, Activities, Actors, 
         Areas, Area, Map, Loader){
  function formatCoords(c){
    return c[0].toFixed(2) + ', ' + c[1].toFixed(2);
  }
  function clearSelect(select){
    for(var i = select.options.length - 1 ; i >= 0 ; i--) { select.remove(i); }
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
     * @param {module:collections/Activities} options.activities       the activities belonging to the keyflow
     * @param {module:collections/AreaLevels} options.areaLevels       the levels of areas belonging to the casestudy of the keyflow (sorted ascending by level, starting with top-level)
     * @param {Object} options.focusarea                               geojson with multipolygon that will be drawn on the map
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
      this.focusarea = options.focusarea;
      this.areaLevels = options.areaLevels;
      
      this.layers = {
        operational: {
          pin: '/static/img/simpleicon-places/svg/map-marker-red.svg',
          style: {
            stroke: 'rgb(255, 51, 0)',
            fill: 'rgba(255, 51, 0, 0.1)',
            strokeWidth: 1
          }
        },
        administrative: {
          pin: '/static/img/simpleicon-places/svg/map-marker-blue.svg',
          style: {
            stroke: 'rgb(51, 153, 255)',
            fill: 'rgba(51, 153, 255, 0.1)'
          }
        },
        background: {
          style: {
            stroke: '#aad400',
            fill: 'rgba(170, 212, 0, 0.1)'
          }
        }
      };
      
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
      
      var topLevel = this.areaLevels.first();
      this.topLevelAreas = new Areas([], { caseStudyId: caseStudyId, levelId: topLevel.id })
        
      $.when(this.adminLocations.fetch({ data: { actor: this.model.id } }), 
             this.opLocations.fetch({ data: { actor: this.model.id } }),
             this.topLevelAreas.fetch()).then(function() {
          _this.topLevelAreas.sort();
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
      this.renderAreaInput();
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
      
      this.globalMap = new Map({
        divid: 'actors-map', 
      });
      
     this.localMap = new Map({
        divid: 'edit-location-map', 
      });
      
      _.each(this.layers, function(attrs, layername){
        _this.globalMap.addLayer(layername, attrs.style);
        _this.localMap.addLayer(layername, attrs.style);
      });
      
      // event triggered when modal dialog is ready -> trigger rerender to match size
      $('#location-modal').on('shown.bs.modal', function () {
        _this.localMap.map.updateSize();
     });
    },
    
    /* 
     * add a location to the map
     */
    addLocation: function(coord, locations, layername, table){
      var properties = {actor: this.activeActorId}
      var loc = new locations.model({}, {caseStudyId: this.model.get('casestudy'),
                                          type: locations.loc_type,
                                          properties: properties})
      loc.setGeometry(coord);
      locations.add(loc);
      this.renderLocation(loc, layername, table);
    },
    
    /* 
     * add a marker with given location to the map and the table
     */
    renderLocation: function(loc, layername, table){ 
      if (loc == null)
        return;
      /* add table rows */
      
      var row = table.insertRow(-1);
      var _this = this;
      var pin = this.layers[layername].pin;
      
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
      
      // add a marker to the table and the map, if there is a geometry attached to the location
      var markerCell = row.insertCell(-1);
      var geom = loc.get('geometry');
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
          _this.globalMap.center(loc.get('geometry').get('coordinates'), 
                          {projection: _this.projection})
        });
        
        /* add marker */
      
        this.globalMap.addmarker(coords, { 
          icon: pin, 
          //dragIcon: this.pins.orange, 
          projection: this.projection,
          name: loc.get('properties').name,
          onDrag: function(coords){
            loc.get('geometry').set("coordinates", coords);
            coordDiv.innerHTML = '(' + formatCoords(coords) + ')';
          },
          layername: layername
        });
      };
      
      // add area to table and map
      var areaCell = row.insertCell(-1);
      var areaId = loc.get('properties').area,
          levelId = loc.get('properties').level,
          caseStudyId = _this.keyflow.get('casestudy');
      
      if(areaId != null){
        var area = new Area({ id: areaId }, { caseStudyId: caseStudyId, levelId: levelId });
        area.fetch({success: function(){
          var wrapper = document.createElement('span'),
              symbol = document.createElement('div'),
              areanameDiv = document.createElement('div');
          
          symbol.style.float = 'left';
          symbol.classList.add('fa');
          symbol.classList.add('fa-map-o');
          symbol.style.marginRight = '3px';
          symbol.style.fontSize = '1.5em';
          symbol.style.color = _this.layers[layername].style.stroke;
          wrapper.style.whiteSpace = 'nowrap';
          wrapper.style.cursor = 'pointer';
          
          var name = area.get('properties').name;
          if (name && name.length > 15) name = name.substring(0, 15) + '...';
          areanameDiv.innerHTML = name;
          areanameDiv.style.paddingTop = '5px';
          
          wrapper.appendChild(symbol);
          wrapper.appendChild(areanameDiv);
          areaCell.appendChild(wrapper);
          
          var polyCoords = area.get('geometry').coordinates[0];
          var poly = _this.globalMap.addPolygon(polyCoords, { projection: _this.projection, layername: layername });
          // zoom to location if marker in table is clicked 
          areaCell.addEventListener('click', function(){ 
            _this.globalMap.centerOnPolygon(poly, { projection: _this.projection })
          });
        }});
      }
      
      // button for editing the location
      
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
    
    /*
     * create location (administrative or operational) on button click
     */
    createLocationEvent: function(event){
      var buttonId = event.currentTarget.id;
      var properties = {actor: this.model.id};
      var type = (buttonId == 'add-administrative-button') ? 'administrative': 'operational';
      var location = new Geolocation({properties: properties}, 
                                     {caseStudyId: this.keyflow.get('casestudy'),
                                      type: type});
      this.editLocation(location);
    },
    
    /*
     * render the select boxes for areas in the location modal
     */
    renderAreaInput: function(){
      var _this = this;
      var table = document.getElementById('location-area-table');
      this.areaSelects = [];
      var caseStudyId = _this.keyflow.get('casestudy');
      
      function addAreaOptions(areas, select){
        var uop = document.createElement('option');
        uop.selected = true;
        uop.text = gettext('select an area');
        uop.value = -1;
        select.appendChild(uop);
        select.style.maxWidth = '200px';
        areas.each(function(area){
          var option = document.createElement('option');
          option.value = area.id;
          option.text = area.get('name');
          select.appendChild(option);
        });
      };
      
      function setChildSelects(idx){
        // last level has no children itself -> return
        var select = _this.areaSelects[idx];
        if (idx >= _this.areaSelects.length -1 ) return;
        var childSelects = _this.areaSelects.slice(idx + 1);
        // clear all selects hierarchally below this level
        _.each(childSelects, function(sel){
          clearSelect(sel);
        });
        if (select.value == -1) return;
        var directChild = childSelects[0];
        var childAreas = new Areas([], { 
          caseStudyId: caseStudyId, levelId: directChild.levelId 
        });
        childAreas.fetch({ 
          data: { parent_id: select.value, parent_level: select.level },
          success: function(){ addAreaOptions(childAreas, directChild); } 
        });
      }
      
      var idx = 0;
      this.areaLevels.each(function(level){
        var row = table.insertRow(-1);
        row.insertCell(-1).innerHTML = level.get('name');
        var select = document.createElement('select');
        select.level = level.get('level');
        select.levelId = level.id;
        _this.areaSelects.push(select);
        row.insertCell(-1).appendChild(select);
        var cur = idx;
        select.addEventListener('change', function(){
          var areaId = select.value;
          _this.localMap.clearLayer('administrative');
          _this.localMap.clearLayer('operational');
          if (areaId >= 0){
            var area = new Area({ id: areaId }, { caseStudyId: caseStudyId, levelId: level.id });
            // fetch geometry of area and draw it on map
            area.fetch({ success: function(){
              var polyCoords = area.get('geometry').coordinates[0];
              var poly = _this.localMap.addPolygon(polyCoords, { projection: _this.projection, layername: 'operational'});
              _this.localMap.centerOnPolygon(poly, { projection: _this.projection })
            }});
          }
          setChildSelects(cur);
        });
        
        idx++;
      });
      if (this.areaSelects.length == 0) return;
      // prefill select of toplevel
      var topLevelSelect = this.areaSelects[0];
      addAreaOptions(this.topLevelAreas, topLevelSelect);
    },
    
    /*
     * initialize the modal for location editing by filling the forms and map with the values of given location
     * open the modal
     */
    editLocation: function(location){
      var _this = this;
      var topLevelSelect = this.areaSelects[0];
      this.editedLocation = location;
      var locationModal = document.getElementById('location-modal');
      var geometry = location.get('geometry');
      var markerId;
      var coordinates = (geometry != null) ? geometry.get("coordinates"): null;
      var type = location.loc_type || location.collection.loc_type;
      
      var pin = this.layers[type].pin;

      var inner = document.getElementById('location-modal-template').innerHTML;
      var template = _.template(inner);
      var html = template({properties: location.get('properties'), 
                           coordinates: (coordinates != null)? formatCoords(coordinates): '-'});
      document.getElementById('location-modal-content').innerHTML = html;
      $(locationModal).modal('show'); 
      
      // reset the map
      this.localMap.clearLayer('operational');
      this.localMap.clearLayer('administrative');
      this.localMap.removeInteractions();
      
      // don't set coordinates directly to location, only on confirmation
      this.tempCoords = coordinates;
      var elGeom = document.getElementById('coordinates');
      
      
      var addPointBtn = locationModal.querySelector('#add-point'),
          removePointBtn = locationModal.querySelector('#remove-point');
      
      // show/hide add/remove point buttons
      function setPointButtons(state){
        if (state == 'add') {
            addPointBtn.style.display = 'block';
            removePointBtn.style.display = 'none';
        }
        else {
            addPointBtn.style.display = 'none';
            removePointBtn.style.display = 'block';
        }
      }
      
      function removeMarkerCallback(){
          _this.tempCoords = null;
          elGeom.innerHTML = '-';
          setPointButtons('add');
      }
      
      // add a marker to map
      function addMarker(coords){
        elGeom.innerHTML = formatCoords(coords);
        markerId = _this.localMap.addmarker(coords, { 
          icon: pin, 
          //dragIcon: this.pins.orange, 
          projection: _this.projection,
          name: location.get('properties').name,
          onDrag: function(coords){
            _this.tempCoords = coords;
            elGeom.innerHTML = formatCoords(coords);
          },
          onRemove: removeMarkerCallback,
          removable: true,
          layername: type
        });
        _this.localMap.center(coords, {projection: _this.projection});
      }
      
      // connect add/remove point buttons
      var center = this.centroid || [13.4, 52.5];
      addPointBtn.addEventListener('click', function(){ 
        _this.tempCoords = center;
        addMarker(center);
        setPointButtons('remove');
      });
      removePointBtn.addEventListener('click', function(){
        _this.localMap.clearLayer(type);
        _this.localMap.removeInteractions();
        removeMarkerCallback();
      });
      
      // initially set marker depending on existing geometry
      if (coordinates != null){
        addMarker(coordinates);
        setPointButtons('remove');
      }
      else 
        setPointButtons('add');
        
      // context menu with add/remove
      var items = [
        {
          text: 'Set Location',
          icon: pin,
          callback: function(event){
            var coords = _this.localMap.toProjection(event.coordinate, _this.projection);
            if (_this.tempCoords != null){
              _this.localMap.moveMarker(markerId, event.coordinate, { layername: type });
              elGeom.innerHTML = formatCoords(coords);
            }
            else{
              addMarker(coords);
              setPointButtons('remove');
            }
            _this.tempCoords = coords;
          }
        },
        '-'
      ];
      this.localMap.addContextMenu(items);
    },
    
    /*
     * called when the location modal is confirmed by the user
     * set the changes made to the edited location
     */
    locationConfirmed: function(){
      var location = this.editedLocation;
      if(location == null) return;
      
      var geometry = location.get('geometry');
      if (geometry != null) geometry.set("coordinates", this.tempCoords);
      else location.setGeometry(this.tempCoords)
      var form = document.getElementById('location-modal-content');
      var inputs = form.querySelectorAll('input');
      var properties = location.get('properties');
      _.each(inputs, function(input){
        //properties.set(input.name) = input.value;
        properties[input.name] = input.value;
      });
      
      var areaTable = document.getElementById('location-area-table');
      var selects = areaTable.querySelectorAll('select');
      var areaId = null,
          levelId = null;
      // iterate area-selects (sorted hierarchally) and take last one that is filled
      for(var i = 0; i < selects.length; i++){
        var select = selects[i];
        // -1 is "select an area", meaning it is not set
        if (select.value < 0) break;
        areaId = select.value;
        levelId = select.levelId;
      }
      properties.area = areaId;
      properties.level = levelId;
      
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
      
      this.globalMap.clearLayer('administrative');
      this.globalMap.clearLayer('operational');
      this.renderLocation(adminLoc, 'administrative', this.adminTable);
      this.opLocations.each(function(loc){_this.renderLocation(loc, 'operational', _this.opTable);});
      
      var addAdminBtn = document.getElementById('add-administrative-button');
      if (adminLoc != null){
        // you may not have more than one admin. location (hide button, if there already is one)
        addAdminBtn.style.display = 'none';
        var geom = adminLoc.get('geometry');
      }
      else addAdminBtn.style.display = 'block';
      
      // add polygon of focusarea to both maps and center on their centroid
      if (this.focusarea != null){
        var poly = this.globalMap.addPolygon(this.focusarea.coordinates[0], { projection: this.projection, layername: 'background' });
        this.localMap.addPolygon(this.focusarea.coordinates[0], { projection: this.projection, layername: 'background' });
        this.globalMap.centerOnPolygon(poly, { projection: _this.projection });
        this.localMap.centerOnPolygon(poly, { projection: _this.projection });
      };
    },
    
    toggleIncluded: function(event){
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