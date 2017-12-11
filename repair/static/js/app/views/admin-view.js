define(['backbone', 'app/models/casestudy', 'app/views/admin-data-entry',
        'app/views/admin-data-view', 'app/views/admin-edit-actors', 
        'app/collections/flows', 'app/collections/activities', 'app/collections/actors',
        'app/collections/activitygroups', 'app/collections/keyflows',
        'app/collections/stocks', 'app/collections/materials',
        'app/collections/products', 'app-config', 'app/loader'],
function(Backbone, CaseStudy, DataEntryView, DataView, EditActorsView, Flows, 
         Activities, Actors, ActivityGroups, Keyflows, Stocks, Materials,
         Products, appConfig){

  var AdminView = Backbone.View.extend({

    initialize: function(options){
      _.bindAll(this, 'render');
      
    },

    events: {
    },

    render: function(){
      var template = document.getElementById(this.template);
      this.el.innerHTML = template.innerHTML;

    },

    /*
      * remove this view from the DOM
      */
    close: function(){
      this.undelegateEvents(); // remove click events
      this.unbind(); // Unbind all local event bindings
      this.el.innerHTML = ''; // Remove view from DOM
    },
  });

  return AdminView;
}
);