define(['backbone', 'app/models/activitygroup', 'app/models/activity', 
        'app/models/actor'],
  function(Backbone, Sankey, DataTree, ActivityGroup, Activity, Actor){
    var EditNodeView = Backbone.View.extend({

      initialize: function(options){
        _.bindAll(this, 'render');
        this.template = options.template;
        this.material = options.material;
        this.render();
      },

      render: function(){
        var html = document.getElementById(this.template).innerHTML
        var template = _.template(html);
        this.el.innerHTML = template();
        
        var attrDiv = document.getElementById('attributes');
        var inner = '';
        if (this.model.tag == 'activity') 
          inner = this.getActivityAttrTable();
        else if (this.model.tag == 'activitygroup')
          inner = this.getGroupAttrTable();
        else if (this.model.tag == 'actor') 
          inner = this.getActorAttrTable();
        console.log(inner)
        attrDiv.innerHTML = inner;
      },
      
      getGroupAttrTable: function(){
        var html = document.getElementById('group-attributes-template').innerHTML
        var template = _.template(html);
        return template({
          name: this.model.get('name'),
          material: this.material,
          code: this.model.get('code')
        });
      },
      
      getActivityAttrTable: function(){
        var html = document.getElementById('activity-attributes-template').innerHTML
        var template = _.template(html);
        return template({
          name: this.model.get('name'),
          material: this.material,
          group: this.model.get('own_activitygroup'),
          nace: this.model.get('nace')
        });
      },
      
      getActorAttrTable: function(){
        var html = document.getElementById('actor-attributes-template').innerHTML
        var template = _.template(html);
        return template({
          name: this.model.get('name'),
          material: this.material,
          bvdid: this.model.get('BvDid'),
          activity: this.model.get('own_activity'),
          url: this.model.get('website'),
          year: this.model.get('year'),
          employees: this.model.get('employees'),
          revenue: this.model.get('revenue')
        });
      },

      close: function(){
        this.unbind(); // Unbind all local event bindings
        //this.remove(); // Remove view from DOM
        this.el.innerHTML = ''; //empty the DOM element
      },

    });
    return EditNodeView;
  }
);