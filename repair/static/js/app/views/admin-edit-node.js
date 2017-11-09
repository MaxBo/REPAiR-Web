define(['jquery', 'backbone', 'app/models/activitygroup', 'app/models/activity',
        'app/models/actor', 'app/collections/flows', 'app/loader'],
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
function($, Backbone, ActivityGroup, Activity, Actor, Flows){
  var EditNodeView = Backbone.View.extend({

    /*
      * view-constructor
      */
    initialize: function(options){
      _.bindAll(this, 'render');
      this.template = options.template;
      this.materialId = options.materialId;
      this.caseStudyId = options.caseStudyId;
      this.qualities = options.qualities;
      
      var flowType = '';
      this.attrTableInner = '';
      if (this.model.tag == 'activity'){
        this.attrTableInner = this.getActivityAttrTable();
        flowType = 'activity2activity';
      }
      else if (this.model.tag == 'activitygroup'){
        this.attrTableInner = this.getGroupAttrTable();
        flowType = 'activitygroup2activitygroup';
      }
      else if (this.model.tag == 'actor'){
        this.attrTableInner = this.getActorAttrTable();
        flowType = 'actor2actor';
      }
      
      this.inFlows = new Flows({caseStudyId: this.caseStudyId, 
                                materialId: this.materialId,
                                type: flowType});
      this.outFlows = new Flows({caseStudyId: this.caseStudyId, 
                                 materialId: this.materialId,
                                 type: flowType});
      var _this = this;
      
      var loader = new Loader(this.el);
      // fetch inFlows and outFlows with different query parameters
      this.inFlows.fetch({
        data: 'destination=' + this.model.id,
        success: function(){
          _this.outFlows.fetch({
            data: 'origin=' + _this.model.id,
            success: function(){
              loader.remove();
              _this.render();
            }
          })
        }
      });
    },

    /*
      * dom events (managed by jquery)
      */
    events: {
      'click #upload-flows-button': 'uploadChanges'
      //'click #add-input-button, #add-stock-button, #add-output-button': 'addRowEvent',
      //'click #remove-input-button, #remove-stock-button, #remove-output-button': 'deleteRowEvent'
    },

    /*
      * render the view
      */
    render: function(){
      var _this = this;
      console.log(this.model.collection);
      var html = document.getElementById(this.template).innerHTML
      var template = _.template(html);
      this.el.innerHTML = template();

      // temp. disabled
      this.el.querySelector('#add-stock-button').disabled = true;
      this.el.querySelector('#remove-stock-button').disabled = true;

      // render a view on the attributes depending on type of node
      var attrDiv = this.el.querySelector('#attributes');
      attrDiv.innerHTML = this.attrTableInner;
      
      // render inFlows
      this.inFlows.each(function(flow){
        _this.addFlowRow('input-table', flow, 'origin');
      });
      this.outFlows.each(function(flow){
        _this.addFlowRow('output-table', flow, 'destination');
      });
    },
    
    addFlowRow: function(tableId, flow, identifier){
      var _this = this;

      var table = this.el.querySelector('#' + tableId);
      var row = table.insertRow(-1);
      
      // checkbox for marking deletion
      
      var checkbox = document.createElement("input");
      checkbox.type = 'checkbox';
      row.insertCell(-1).appendChild(checkbox);
      
      checkbox.addEventListener('change', function() {
        row.classList.toggle('strikeout');
      });
      
      // amount of flow
      
      var amount = document.createElement("input");
      amount.value = flow.get('amount');
      amount.type = 'number';
      amount.min = 0;
      row.insertCell(-1).appendChild(amount);
      
      amount.addEventListener('change', function() {
        flow.set('amount', amount.value);
      });
      
      // select input for target (origin resp. destination of flow)
      
      var nodeSelect = document.createElement("select");
      var ids = [];
      var targetId = flow.get(identifier);
      this.model.collection.each(function(model){
        // no flow to itself allowed
        if (model.id != _this.model.id){
          var option = document.createElement("option");
          option.text = model.get('name');
          option.value = model.id;
          nodeSelect.add(option);
          ids.push(model.id);
        };
      });
      var idx = ids.indexOf(targetId);
      nodeSelect.selectedIndex = idx.toString();
      row.insertCell(-1).appendChild(nodeSelect);
      
      nodeSelect.addEventListener('change', function() {
        console.log(nodeSelect.value);
      });
      
      // select input for qualities
      
      var qualitySelect = document.createElement("select");
      var ids = [];
      var q = flow.get('quality');
      this.qualities.each(function(quality){
        var option = document.createElement("option");
        option.text = quality.get('name');
        option.value = quality.id;
        qualitySelect.add(option);
        ids.push(quality.id);
      });
      var idx = ids.indexOf(q);
      qualitySelect.selectedIndex = idx.toString();
      row.insertCell(-1).appendChild(qualitySelect);
      
      qualitySelect.addEventListener('change', function() {
        console.log(qualitySelect.value);
      });
      
      // THERE IS NO FIELD FOR THIS! (but represented in Rusnes layout)
      var description = document.createElement("input");
      row.insertCell(-1).appendChild(description);
      
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
        this.model.collection.each(function(m){names.push(m.get('name'))});
        var node = {type: 'select', text: names, value: names};
        columns.push(node);
      }

      var qualities = {type: 'select', text: [1, 2, 3, 4]};
      columns.push(qualities);
    },


    /**
    * add a row to the given table
    *
    * @param tableId  id of the table to add a row to
    * @param columns  array of objects to put in each column
    *                 attributes of object: type (optional)  - 'select'/'number'/'text'
    *                                       value (required) - single value or array (array for select only)
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
            for (j = 0; j < column.text.length; j++){
              var option = document.createElement("option");
              option.text = column.text[j];
              if (column.value != null)
                option.value = column.value[j];
              child.add(option);
            }
            if (column.selected != null)
              child.selectedIndex = column.selected.toString();
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
      return row;
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
    
    uploadChanges: function(){
      this.inFlows.each(function(model){
        model.save();
      });
      //this.outFlows.save();
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