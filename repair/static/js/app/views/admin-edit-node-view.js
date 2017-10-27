define(['backbone', 'app/models/activitygroup', 'app/models/activity', 
        'app/models/actor'],
  /** 
   * 
   * @desc    view on edit a specific node
   * 
   * @param   options.el        html-element the view will be rendered in
   * @param   options.model     backbone-model of the node
   * @param   options.template  the id of the script containing the template for this view
   * @param   options.material  the material of the flows
   * 
   * @return  the EditNodeView class (for chaining)
   * @see     table for attributes and flows in and out of this node
   */
  function(Backbone, Sankey, DataTree, ActivityGroup, Activity, Actor){
    var EditNodeView = Backbone.View.extend({

      /*
       * view-constructor
       */
      initialize: function(options){
        _.bindAll(this, 'render');
        this.template = options.template;
        this.material = options.material;
        this.render();
      },
      
      /*
       * dom events (managed by jquery)
       */
      events: {
        'click #add-input-button, #add-stock-button, #add-output-button': 'addRowEvent'
      },

      /*
       * render the view
       */ 
      render: function(){
        var html = document.getElementById(this.template).innerHTML
        var template = _.template(html);
        this.el.innerHTML = template();
        
        // render a view on the attributes depending on type of node
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
      
      // on click add row button
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
    
      /**
      * add a row to the given table
      *
      * @param tableId        id of the table to add a row to
      * @param rowTemplateId  template for the row to add
      * @param options        variables and their values to inject into the template
      */
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

      /*
       * remove this view from the DOM
       */
      close: function(){
        this.undelegateEvents(); // remove click events
        this.unbind(); // Unbind all local event bindings
        this.el.innerHTML = ''; //empty the DOM element
      },

    });
    return EditNodeView;
  }
);