define(['backbone', 'app/models/activitygroup', 'app/models/activity',
        'app/models/actor', 'app/collections/flows', 'app/collections/stocks',
        'app/loader', 'bootstrap'],
/**
  *
  * @desc    view on edit a specific node
  *
  * @param   options.el        html-element the view will be rendered in
  * @param   options.model     backbone-model of the node
  * @param   options.template  the id of the script containing the template for this view
  * @param   options.keyflow   the keyflow of the flows
  *
  * @return  the EditNodeView class (for chaining)
  * @see     table for attributes and flows in and out of this node
  */
function(Backbone, ActivityGroup, Activity, Actor, Flows, Stocks){
  var EditNodeView = Backbone.View.extend({

    /*
      * view-constructor
      */
    initialize: function(options){
      _.bindAll(this, 'render');
      this.template = options.template;
      this.keyflowId = options.keyflowId;
      this.keyflowName = options.keyflowName;
      this.caseStudyId = options.caseStudyId;
      this.products = options.products;
      this.materials = options.materials;
      console.log(this.products)
      console.log(this.materials)
      
      this.onUpload = options.onUpload;

      var flowType = '';
      this.attrTableInner = '';
      if (this.model.tag == 'activity'){
        this.attrTableInner = this.getActivityAttrTable();
        flowType = 'activity';
      }
      else if (this.model.tag == 'activitygroup'){
        this.attrTableInner = this.getGroupAttrTable();
        flowType = 'activitygroup';
      }
      else if (this.model.tag == 'actor'){
        this.attrTableInner = this.getActorAttrTable();
        flowType = 'actor';
      }

      this.inFlows = new Flows([], {caseStudyId: this.caseStudyId,
                                    keyflowId: this.keyflowId,
                                    type: flowType});
      this.outFlows = new Flows([], {caseStudyId: this.caseStudyId,
                                      keyflowId: this.keyflowId,
                                      type: flowType});
      this.stocks = new Stocks([], {caseStudyId: this.caseStudyId,
                                    keyflowId: this.keyflowId,
                                    type: flowType});
      this.newInFlows = new Flows([], {caseStudyId: this.caseStudyId,
                                        keyflowId: this.keyflowId,
                                        type: flowType});
      this.newOutFlows = new Flows([], {caseStudyId: this.caseStudyId,
                                        keyflowId: this.keyflowId,
                                        type: flowType});
      this.newStocks = new Stocks([], {caseStudyId: this.caseStudyId,
                                      keyflowId: this.keyflowId,
                                      type: flowType});
      var _this = this;

      var loader = new Loader(document.getElementById('flows-edit'),
                              {disable: true});
      // fetch inFlows and outFlows with different query parameters

      $.when(this.inFlows.fetch({data: 'destination=' + this.model.id}),
             this.outFlows.fetch({data: 'origin=' + this.model.id}),
             this.stocks.fetch({data: 'origin=' + this.model.id})).then(function() {
          loader.remove();
          _this.render();
      });
    },

    /*
      * dom events (managed by jquery)
      */
    events: {
      'click #upload-flows-button': 'uploadChanges',
      'click #add-input-button, #add-output-button, #add-stock-button': 'addFlowEvent'
      //'click #remove-input-button, #remove-stock-button, #remove-output-button': 'deleteRowEvent'
    },

    /*
      * render the view
      */
    render: function(){
      var _this = this;
      var html = document.getElementById(this.template).innerHTML
      var template = _.template(html);
      this.el.innerHTML = template();

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
      this.stocks.each(function(stock){
        _this.addFlowRow('stock-table', stock, 'origin', true);
      });
    },

    addFlowRow: function(tableId, flow, targetIdentifier, skipTarget){
      var _this = this;

      var table = this.el.querySelector('#' + tableId);
      var row = table.insertRow(-1);

      // checkbox for marking deletion

      var checkbox = document.createElement("input");
      checkbox.type = 'checkbox';
      row.insertCell(-1).appendChild(checkbox);

      checkbox.addEventListener('change', function() {
        row.classList.toggle('strikeout');
        flow.markedForDeletion = checkbox.checked;
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

      if (!skipTarget){
        // select input for target (origin resp. destination of flow)

        var nodeSelect = document.createElement("select");
        var ids = [];
        var targetId = flow.get(targetIdentifier);
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
          flow.set(targetIdentifier, nodeSelect.value);
        });
      };
      
      // input for product
      var productSelect = document.createElement("select");
      var ids = [];
      var p = flow.get('product');
      this.products.each(function(product){
        var option = document.createElement("option");
        option.text = product.get('name');
        option.value = product.id;
        productSelect.add(option);
        ids.push(product.id);
      });
      var idx = ids.indexOf(p);
      productSelect.selectedIndex = idx.toString();
      cell = row.insertCell(-1); 
      cell.appendChild(productSelect);

      productSelect.addEventListener('change', function() {
        flow.set('product', productSelect.value);
      });
      
      // information popup for products
      var info = document.createElement('div');
      info.style.cursor = 'pointer';
      info.style.marginLeft = "5px";
      info.classList.add('pop-function');
      info.setAttribute('rel', 'popover');
      info.classList.add('glyphicon');
      info.classList.add('glyphicon-info-sign');
      info.title = 'composition of product';
      cell.appendChild(info);
      
      var popOverSettings = {
          placement: 'right',
          container: 'body',
          trigger: 'hover',
          html: true,
          content: function () {
              var product = _this.products.get(productSelect.value);
              var html = document.getElementById('popover-product-template').innerHTML;
              var template = _.template(html);
              var content = template({fractions: product.get('fractions'), 
                                      materials: _this.materials});
              return content;
          }
      }
      $(info).popover(popOverSettings);
      

      // THERE IS NO FIELD FOR THIS! (but represented in Rusnes layout)
      var description = document.createElement("textarea");
      description.rows = "1";
      //description.style.resize = 'both';
      row.insertCell(-1).appendChild(description);

      description.addEventListener('change', function() {
        flow.set('description', description.value);
      });

      // general datasource
      var options = ['dummy-source', 'another dummy-source']
      var datasource = document.createElement("select");
      _.each(options, function(opt){
        var option = document.createElement("option");
        option.text = opt;
        option.value = opt;
        datasource.add(option);
      });
      cell = row.insertCell(-1);
      cell.appendChild(datasource);
      var collapse = document.createElement('div');
      collapse.style.cursor = 'pointer';
      var dsRow = table.insertRow(-1);
      
      // collapse icon to show/hide individual datasources
      dsRow.classList.add('hidden');
      collapse.style.marginLeft = "4px";
      collapse.classList.add('glyphicon');
      collapse.title = 'show individual datasources';
      collapse.classList.add('glyphicon-chevron-down');
      collapse.addEventListener('click', function(){
        dsRow.classList.toggle('hidden');
        collapse.classList.toggle('glyphicon-chevron-down');
        collapse.classList.toggle('glyphicon-chevron-up');
      });
      cell.appendChild(collapse);
      
      // own row for individual Datasources
      
      dsRow.insertCell(-1);
      var datasourcableAttributes = ['amount', targetIdentifier, 'description'];
      _.each(datasourcableAttributes, function(attr){
        var sel = document.createElement("select");
        var cell = dsRow.insertCell(-1).appendChild(sel);
        _.each(options, function(opt){
          var option = document.createElement("option");
          option.text = opt;
          option.value = opt;
          cell.add(option);
        });
        // general datasource overrides all sub datasources
        datasource.addEventListener('change', function(){
          sel.selectedIndex = datasource.selectedIndex;
        });
        // sub datasources changes -> show that general datasource is custom by leaving it blank
        sel.addEventListener('change', function(){
          datasource.selectedIndex = -1;
        });
      });
      
      return row;
    },
    
    popupProductInfo: function(productId){
      console.log(productId);
    },

    // on click add row button
    addFlowEvent: function(event){
      var buttonId = event.currentTarget.id;
      var tableId;
      var flow;
      var targetIdentifier;
      var skipTarget = false;
      if (buttonId == 'add-input-button'){
        tableId = 'input-table';
        flow = this.newInFlows.add({});
        targetIdentifier = 'origin';
        flow = this.newOutFlows.add({
          'amount': 0,
          'origin': null,
          'destination': this.model.id,
          'quality': null
        });
      }
      else if (buttonId == 'add-output-button'){
        tableId = 'output-table';
        targetIdentifier = 'destination';
        flow = this.newOutFlows.add({
          'amount': 0,
          'origin': this.model.id,
          'destination': null,
          'quality': null
        });
      }
      else if (buttonId == 'add-stock-button'){
        tableId = 'stock-table';
        targetIdentifier = 'origin';
        flow = this.newStocks.add({
          'amount': 0,
          'origin': this.model.id,
          'quality': null
        });
        skipTarget = true;
      }
      this.addFlowRow(tableId, flow, targetIdentifier, skipTarget);

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
      var rowCount = table.rows.length;

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
        keyflow: this.keyflowName,
        code: this.model.get('code')
      });
    },

    getActivityAttrTable: function(){
      var html = document.getElementById('activity-attributes-template').innerHTML
      var template = _.template(html);
      return template({
        name: this.model.get('name'),
        keyflow: this.keyflowName,
        group: this.model.get('activitygroup'),
        nace: this.model.get('nace')
      });
    },

    getActorAttrTable: function(){
      var html = document.getElementById('actor-attributes-template').innerHTML
      var template = _.template(html);
      return template({
        name: this.model.get('name'),
        keyflow: this.keyflowName,
        bvdid: this.model.get('BvDid'),
        activity: this.model.get('activity'),
        url: this.model.get('website'),
        year: this.model.get('year'),
        employees: this.model.get('employees'),
        turnover: this.model.get('turnover')
      });
    },

    uploadChanges: function(){
      var _this = this;
      
      var modelsToSave = [];
      var modelsToDestroy = [];
      
      // delete exisiting flows if marked for deletion
      // otherwise update them if they changed
      var update = function(model){
        if (model.markedForDeletion)
          modelsToDestroy.push(model);
        else if (model.changedAttributes() != false)
          modelsToSave.push(model);
      };
      this.inFlows.each(update);
      this.outFlows.each(update);
      this.stocks.each(update);

      // save added flows only, when they are not marked for deletion
      var create = function(model){
        console.log(model)
        if (!model.markedForDeletion && Object.keys(model.attributes).length > 0) // sometimes empty models sneak in, not sure why
          modelsToSave.push(model);
      }
      this.newInFlows.each(create);
      this.newOutFlows.each(create);
      this.newStocks.each(create);
      
      // chain save and destroy operations
      var saveComplete = _.invoke(modelsToSave, 'save');
      var destructionComplete = _.invoke(modelsToDestroy, 'destroy');
      
      var loader = new Loader(document.getElementById('flows-edit'),
                              {disable: true});
      var onError = function(response){
        alert(response.responseText); 
        loader.remove();
      };
      $.when.apply($, saveComplete).done(function(){
        $.when.apply($, destructionComplete).done(function(){
          loader.remove();
          console.log('upload complete');
          _this.onUpload();
        }).fail(onError);
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
  return EditNodeView;
}
);