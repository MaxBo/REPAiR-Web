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
      'click #add-actor-button': 'addActorEvent'
    },

    /*
      * render the view
      */
    render: function(){
      var _this = this;
      var html = document.getElementById(this.template).innerHTML
      var template = _.template(html);
      this.el.innerHTML = template({casestudy: this.model.get('name')});

      // render inFlows
      this.collection.each(function(actor){_this.addActorRow(actor)}); // you have to define function instead of passing this.addActorRow, else scope is wrong
    },

    addActorRow: function(actor){
      console.log(actor)
      var _this = this;

      var table = this.el.querySelector('#actors-table');
      var row = table.insertRow(-1);

      // checkbox for marking deletion

      var checkbox = document.createElement("input");
      checkbox.type = 'checkbox';
      row.insertCell(-1).appendChild(checkbox);

      checkbox.addEventListener('change', function() {
        row.classList.toggle('strikeout');
        actor.markedForDeletion = checkbox.checked;
      });
      
      var addInput = function(attribute, inputType){
        var input = document.createElement("input");
        if (inputType == 'number')
          input.type = 'number'
        input.value = actor.get(attribute);
        row.insertCell(-1).appendChild(input);
  
        input.addEventListener('change', function() {
          actor.set(attribute, input.value);
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
        actor.set(activity, activitySelect.value);
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