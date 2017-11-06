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
      'click #add-input-button, #add-stock-button, #add-output-button': 'addRowEvent',
      'click #remove-input-button, #remove-stock-button, #remove-output-button': 'deleteRowEvent'
    },

    /*
      * render the view
      */
    render: function(){
      var html = document.getElementById(this.template).innerHTML
      var template = _.template(html);
      this.el.innerHTML = template();

      // temp. disabled
      this.el.querySelector('#add-stock-button').disabled = true;
      this.el.querySelector('#remove-stock-button').disabled = true;

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
      var columns = [];
      var tableId = (buttonId == 'add-input-button') ? 'input-table':
        (buttonId == 'add-output-button') ? 'output-table':
        'stock-table'

      var checkbox = {type: 'checkbox', value: false};
      columns.push(checkbox);
      var amount = {type: 'number', value: 0, min: 0};
      columns.push(amount);

      // stock has no origin/destination
      if (buttonId == 'add-input-button' || buttonId == 'add-output-button'){
        var names = [];
        this.model.collection.each(function(m){names.push(m.get('name'))})
        var node = {type: 'select', value: names};
        columns.push(node);
      }

      var qualities = {type: 'select', value: [1, 2, 3, 4]};
      columns.push(qualities);
      var description = {type: 'text', value: ''};
      columns.push(description);

      this.addTableRow(tableId, columns)
    },

    /**
    * add a row to the given table
    *
    * @param tableId  id of the table to add a row to
    * @param columns  array of objects to put in each column
    *                 attributes of object: type (optional)  - 'select'/'number'/'text'
    *                                       value (required) - single value or array (select only)
    *                                       min (optional) - min. value (number only)
    *                                       max (optional) - max. value (number only
    *                 (same order in array as in table required)
    */
    addTableRow: function(tableId, columns){
      var table = this.el.querySelector('#' + tableId);
      var row = table.insertRow(-1);
      for (i = 0; i < columns.length; i++){
        var column = columns[i];
        var cell = row.insertCell(i);
        if (column.type != null){
          var child;              
          if (column.type == 'select'){
            child = document.createElement("select");
            for (j = 0; j < column.value.length; j++){
              var option = document.createElement("option");
              option.text = column.value[j];
              child.add(option);
            }
          }
          else{
            var child = document.createElement("input");
            if (column.type == 'number'){
              child.type = "number";
              if (column.min != null) child.min = column.min;
              if (column.max != null) child.max = column.max;
            }
            else if (column.type == 'checkbox')
              child.type = "checkbox";

            child.value = column.value;
          }
          cell.appendChild(child);
        }
        else
          cell.innerHTML = column.value;
      }
    },
    
    deleteRowEvent: function(event){
      var buttonId = event.currentTarget.id;
      var tableId = (buttonId == 'remove-input-button') ? 'input-table':
        (buttonId == 'remove-output-button') ? 'output-table':
        'stock-table';
      this.deleteTableRows(tableId);
    },

    deleteTableRows: function(tableId)  {
      var table = this.el.querySelector('#' + tableId);
      console.log(table)
      var rowCount = table.rows.length;
      console.log(rowCount)

      // var i=1 to start after header
      for(var i = rowCount - 1; i > 0; i--) {
        var row = table.rows[i];
        var checkbox = row.cells[0].getElementsByTagName('input')[0];
        if(checkbox.type == 'checkbox' && checkbox.checked == true) {
          table.deleteRow(i);
        }
      }
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
        group: this.model.get('activitygroup'),
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
        activity: this.model.get('activity'),
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