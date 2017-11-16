define(['jquery', 'backbone', 'app/models/actor', 'app/loader'],

function($, Backbone, Actor){
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
      console.log(this.onUpload)

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

      // render inFlows
      this.collection.each(function(actor){_this.addActorRow(actor)}); // you have to define function instead of passing this.addActorRow, else scope is wrong
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
      
      var row = this.table.insertRow(-1);

      // checkbox for marking deletion

      var checkbox = document.createElement("input");
      checkbox.type = 'checkbox';
      var included = actor.get('included')
      checkbox.checked = included;
      if (!included){
        row.classList.add('strikeout');
        if (!this.showAll)
          row.style.display = "block";
      }
      row.insertCell(-1).appendChild(checkbox);

      checkbox.addEventListener('change', function() {
        row.classList.toggle('strikeout');
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
      addInput('year');
      addInput('revenue');
      addInput('employees');
      addInput('BvDid');
      addInput('BvDii');
      addInput('consCode');

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
        "activity": null
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