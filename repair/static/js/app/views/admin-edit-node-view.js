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
      
      events: {
        'click #add-input-button, #add-stock-button, #add-output-button': 'addRowEvent'
      },

      render: function(){
        var html = document.getElementById(this.template).innerHTML
        var template = _.template(html);
        if (document.getElementById('input-table') != null)
          console.log(document.getElementById('input-table').innerHTML)
        this.el.innerHTML = template();
        
        var attrDiv = this.el.querySelector('#attributes');
        var inner = '';
        if (this.model.tag == 'activity') 
          inner = this.getActivityAttrTable();
        else if (this.model.tag == 'activitygroup')
          inner = this.getGroupAttrTable();
        else if (this.model.tag == 'actor') 
          inner = this.getActorAttrTable();
        attrDiv.innerHTML = inner;
      },
      
      addRowEvent: function(event){
        var buttonId = event.currentTarget.id;
        var rowTemplateId;
        var tableId = (buttonId == 'add-input-button') ? 'input-table': 
                      (buttonId == 'add-output-button') ? 'output-table':
                      'stock-table'
        // common to all tables
        var templateOptions = {
            amount: 0,
            qualities: [1, 2, 3, 4],
            datasource: ''
        };
        // stock has no origin or destination
        if (buttonId == 'add-input-button' || buttonId == 'add-output-button'){
          templateOptions.nodes = this.model.collection;
          rowTemplateId = 'input-output-row';
        }
        else
          rowTemplateId = 'stock-row';
        
        this.addTableRow(tableId, rowTemplateId, templateOptions)
      },
      
      addTableRow: function(tableId, rowTemplateId, options){
          var el = this.el.querySelector('#' + tableId);
          var rowHTML = document.getElementById(rowTemplateId).innerHTML;
          var rowTemplate = _.template(rowHTML);
          el.innerHTML += rowTemplate(options);
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
        this.undelegateEvents();
        this.unbind(); // Unbind all local event bindings
        //this.remove(); // Remove view from DOM
        this.el.innerHTML = ''; //empty the DOM element
      },

    });
    return EditNodeView;
  }
);