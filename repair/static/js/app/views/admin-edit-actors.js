define(['jquery', 'backbone', 'app/models/actor', 'app/visualizations/map', 
        'tablesorter-pager', 'app/loader'],

function($, Backbone, Actor, Map){
  var EditActorsView = Backbone.View.extend({

    /*
      * view-constructor
      */
    initialize: function(options){
      _.bindAll(this, 'render');
      this.template = options.template;
      this.materialId = options.materialId;
      this.activities = options.activities;
      this.showAll = true;
      this.onUpload = options.onUpload;

      var _this = this;

      var loader = new Loader(document.getElementById('actors-edit'),
        {disable: true});
      // fetch inFlows and outFlows with different query parameters

      this.collection.fetch({success: function(){
        loader.remove();
        _this.render();
      }});
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

      //// render inFlows
      this.collection.each(function(actor){_this.addActorRow(actor)}); // you have to define function instead of passing this.addActorRow, else scope is wrong
  
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
        widgets: ['zebra']
      }).tablesorterPager({container: $("#pager")});
      
      // workaround for a bug in tablesorter-pager by triggering
      // event that pager-selection changed to redraw number of visible rows
      var sel = document.getElementById('pagesize');
      sel.selectedIndex = 0;
      sel.dispatchEvent(new Event('change'));
      
      this.map = new Map({
        divid: 'actors-map', 
        //baseLayers: {"Stamen map tiles": new L.tileLayer('http://{s}tile.stamen.com/toner-lite/{z}/{x}/{y}.png', {
              //subdomains: ['','a.','b.','c.','d.'],
              //attribution: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC BY SA</a>'
            //})},
        //overlayLayers: {}
      });
    },

    changeFilter: function(event){
      this.showAll = event.target.value == '0';
      for (var i = 1, row; row = this.table.rows[i]; i++) {
        //console.log(row.cells[0].getElementsByTagName("input")[0])
        //console.log(row.cells[0].getElementsByTagName("input")[0].checked)
        if (!this.showAll && !row.cells[0].getElementsByTagName("input")[0].checked)
          row.style.display = "none";
        else
          row.style.display = "table-row";
      }
    },

    addActorRow: function(actor){
      var _this = this;

      var row = this.table.getElementsByTagName('tbody')[0].insertRow(-1);

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
      addInput('revenue', 'number');
      addInput('employees', 'number');
      addInput('BvDid');
      addInput('BvDii');
      addInput('consCode');
      
      row.addEventListener('click', function() {
        var selected = _this.table.getElementsByClassName("selected");
        _.each(selected, function(row){
          row.classList.remove('selected');
        });
        row.classList.add('selected');
        _this.map.removeMarkers();
        _this.map.addMarker();
      });

    },

    // on click add row button
    addActorEvent: function(event){
      var buttonId = event.currentTarget.id;
      var tableId;
      var actor = new Actor({
        "BvDid": "",
        "name": "",
        "consCode": "",
        "year": 0,
        "revenue": 0,
        "employees": 0,
        "BvDii": "",
        "website": "",
        "activity": null,
        "caseStudyId": this.model.id
      });
      this.collection.add(actor);
      this.addActorRow(actor);

    },

    uploadChanges: function(){

      var _this = this;

      var modelsToSave = [];

      var update = function(model){
        if (model.changedAttributes() != false && Object.keys(model.attributes).length > 0)
          modelsToSave.push(model);
      };
      this.collection.each(update);
      console.log(modelsToSave)

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