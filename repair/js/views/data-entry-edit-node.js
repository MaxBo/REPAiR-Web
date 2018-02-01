define(['backbone', 'underscore', 'models/activitygroup', 'models/activity',
        'models/actor', 'collections/flows', 'collections/stocks',
        'collections/products', 'collections/wastes',
        'utils/loader', 'tablesorter'],
function(Backbone, _, ActivityGroup, Activity, Actor, Flows, Stocks, Products,
         Wastes, Loader){
  /**
   *
   * @author Christoph Franke
   * @name module:views/EditNodeView
   * @augments Backbone.View
   */
  function clearSelect(select, stop){
    var stop = stop || 0;
    for(var i = select.options.length - 1 ; i >= stop ; i--) { select.remove(i); }
  }
  var EditNodeView = Backbone.View.extend(
    /** @lends module:views/EditNodeView.prototype */
    {


  /**
   * callback for uploading the flows
   *
   * @callback module:views/EditNodeView~onUpload
   */
     
  /**
    * render view to edit the flows of a single node (actor, activity or activitygroup)
    *
    * @param {Object} options
    * @param {HTMLElement} options.el                                element the view will be rendered in
    * @param {string} options.template                               id of the script element containing the underscore template to render this view
    * @param {module:models/Actor|module:models/Activity|module:models/ActivityGroup} options.model the node to edit
    * @param {string} options.caseStudyId                            the id of the casestudy the node belongs to
    * @param {string} options.keyflowId                              the id of the keyflow the node belongs to
    * @param {string} options.keyflowName                            the name of the keyflow
    * @param {module:collections/Materials} options.materials        the available materials
    * @param {module:collections/Publications} options.publications  the available publications
    * @param {module:views/EditNodeView~onUpload=} options.onUpload  called after successfully uploading the flows
    *
    * @constructs
    * @see http://backbonejs.org/#View
    */
    initialize: function(options){
      _.bindAll(this, 'render');
      this.template = options.template;
      this.keyflowId = options.keyflowId;
      this.keyflowName = options.keyflowName;
      this.caseStudyId = options.caseStudyId;
      this.materials = options.materials;
      this.publications = options.publications;
      
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
      
      this.outProducts = new Products([], {
        state: {
          pageSize: 1000000,
          firstPage: 1,
          currentPage: 1
        }
      });
      this.outWastes = new Wastes([], {
        state: {
          pageSize: 1000000,
          firstPage: 1,
          currentPage: 1
        }
      });
      
      var _this = this;

      var loader = new Loader(document.getElementById('flows-edit'),
                              {disable: true});
      // fetch inFlows and outFlows with different query parameters
      var nace = this.model.get('nace') || 'None';
      nace = 'T-9700';

      $.when(this.inFlows.fetch({ data: { destination: this.model.id } }),
             this.outFlows.fetch({ data: { origin: this.model.id } }),
             this.stocks.fetch({ data: { origin: this.model.id } }),
             this.outProducts.getFirstPage({ data: { nace: nace } }),
             this.outWastes.getFirstPage({ data: { nace: nace } })).then(function() {
          loader.remove();
          _this.render();
      });
    },

    /*
      * dom events (managed by jquery)
      */
    events: {
      'click #upload-flows-button': 'uploadChanges',
      'click #add-input-button, #add-output-button, #add-stock-button': 'addFlowEvent',
      'click #confirm-datasource': 'confirmDatasource',
      'click #confirm-fractions': 'confirmFractions',
      'click #refresh-publications-button': 'refreshDatasources'
    },

    /*
      * render the view
      */
    render: function(){
      var _this = this;
      var html = document.getElementById(this.template).innerHTML
      var template = _.template(html);
      this.el.innerHTML = template({name: this.model.get('name')});
      
      this.dsTable = document.getElementById('publications-table');
      
      var popOverSettings = {
          placement: 'right',
          container: 'body',
          trigger: 'manual',
          html: true,
          content: this.attrTableInner
      }
      require('bootstrap');
      this.setupPopover($('#node-info-popover').popover(popOverSettings));

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
      
      this.renderDatasources(this.publications);
      this.setupDsTable();
    },
    
    /* set a (jQuery) popover-element to appear on hover and stay visible on hovering popover */
    setupPopover: function(el){
      el.on("mouseenter", function () {
        var _this = this;
        $(this).popover("show");
        $(".popover").on("mouseleave", function () {
          $(_this).popover('hide');
        });
      }).on("mouseleave", function () {
        var _this = this;
        setTimeout(function () {
          if (!$(".popover:hover").length) {
            $(_this).popover("hide");
          }
        }, 300);
      });
    },

    // add a flow to table (which one is depending on type of flow)
    // targetIdentifier is the attribute of the flow with the id of the node connected with this node 
    // set isStock to True for stocks
    addFlowRow: function(tableId, flow, targetIdentifier, isStock){
      var _this = this;

      var table = this.el.querySelector('#' + tableId);
      var row = table.insertRow(-1);

      // checkbox for marking deletion

      var checkbox = document.createElement("input");
      checkbox.type = 'checkbox';
      row.insertCell(-1).appendChild(checkbox);

      checkbox.addEventListener('change', function() {
        row.classList.toggle('strikeout');
        row.classList.toggle('dsbld');
        flow.markedForDeletion = checkbox.checked;
      });
      
      /* add an input-field to the row, 
       * tracking changes made by user to the attribute and automatically updating the model 
       */
      var addInput = function(attribute, inputType){
        var input = document.createElement("input");
        if (inputType != null)
          input.type = inputType;
        input.value = flow.get(attribute);
        row.insertCell(-1).appendChild(input);

        input.addEventListener('change', function() {
          flow.set(attribute, input.value);
        });
        return input;
      };

      var amount = addInput('amount', 'number');
      amount.min = 0;
      
      // origin respectively destination (skipped at stocks)

      if (!isStock){
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
      
      var itemWrapper = document.createElement("span");
      // prevent breaking 
      itemWrapper.setAttribute("style", "white-space: nowrap");
      row.insertCell(-1).appendChild(itemWrapper); 
      
      // input for product
      var typeSelect = document.createElement("select");
      var wasteOption = document.createElement("option")
      wasteOption.value = 'true'; wasteOption.text = gettext('Waste');
      typeSelect.appendChild(wasteOption);
      var productOption = document.createElement("option")
      productOption.value = 'false'; productOption.text = gettext('Product');
      typeSelect.appendChild(productOption);
      typeSelect.value = flow.get('waste');
            
      typeSelect.addEventListener('change', function() {
        flow.set('waste', typeSelect.value);
      });
      
      itemWrapper.appendChild(typeSelect);
      
      var editFractionsBtn = document.createElement('button');
      var pencil = document.createElement('span');
      editFractionsBtn.classList.add('btn', 'btn-primary', 'square');
      editFractionsBtn.appendChild(pencil);
      editFractionsBtn.innerHTML = gettext('Fractions');
      
      itemWrapper.appendChild(editFractionsBtn);
      
      editFractionsBtn.addEventListener('click', function(){
        if (flow.get('waste') == null) return;
        // the nace of this node determines the items for stocks and outputs
        if (targetIdentifier == 'destination' || isStock == true){
          var items = (flow.get('waste') == 'true') ? _this.outWastes : _this.outProducts;
          _this.editFractions(flow, items);
        }
        // take nace of origin node in case of inputs
        else {
          var origin = _this.model.collection.get(flow.get('origin'));
          if (origin == null) return;
          var options = { 
            state: {
              pageSize: 1000000,
              firstPage: 1,
              currentPage: 1
            }
          };
          var nace = origin.get('nace') || 'None';
          var loader = new Loader(document.getElementById('flows-edit'),
                                  {disable: true});
          var items = (flow.get('waste') == 'true') ? new Wastes([], options): new Products([], options);
          items.getFirstPage({ data: { nace: nace } }).then( 
            function(){ _this.editFractions(flow, items); loader.remove(); }
          )
          
        }
      })
      
      // information popup for fractions
      var popOverFractionsSettings = {
          placement: 'right',
          container: 'body',
          trigger: 'hover',
          html: true,
          content: function () {
              var composition = flow.get('composition') || {};
              var html = document.getElementById('popover-fractions-template').innerHTML;
              var template = _.template(html);
              var content = template({ 
                title: composition.name,
                fractions: composition.fractions, 
                materials: _this.materials
              });
              return content;
          }
      }
      
      $(editFractionsBtn).popover(popOverFractionsSettings);
      
      
      // raw checkbox
      
      var rawCheckbox = document.createElement("input");
      rawCheckbox.type = 'checkbox';
      row.insertCell(-1).appendChild(rawCheckbox);

      rawCheckbox.addEventListener('change', function() {
        flow.set('raw', rawCheckbox.checked);
      });
      
      var year = addInput('year', 'number');
      year.min = 0;
      year.max = 3000;
      
      // description field
      
      var description = document.createElement("textarea");
      description.rows = "1";
      description.value = flow.get('description');
      //description.style.resize = 'both';
      row.insertCell(-1).appendChild(description);

      description.addEventListener('change', function() {
        flow.set('description', description.value);
      });
      
      // general datasource
      
      var sourceWrapper = document.createElement("div");
      sourceWrapper.style.float = 'left';
      var sourceCell = row.insertCell(-1);
      // prevent breaking 
      sourceCell.setAttribute("style", "white-space: nowrap");
      var genSource = document.createElement('input');
      var pubId = flow.get('publication');
      if (pubId){
        var publication = this.publications.get(pubId)
        var title = publication.get('title');
        genSource.value = title;
      }
      genSource.disabled = true;
      genSource.style.cursor = 'pointer';
      var editBtn = document.createElement('button');
      var pencil = document.createElement('span');
      editBtn.classList.add('btn', 'btn-primary', 'square');
      editBtn.appendChild(pencil);
      editBtn.title = gettext('edit datasource');
      pencil.classList.add('glyphicon', 'glyphicon-pencil');
      function onChange(publication){
        if (publication != null){
          var title = publication.get('title');
          genSource.value = title;
          flow.set('publication', publication.id)
          genSource.dispatchEvent(new Event('change'));
        }
      };
      editBtn.addEventListener('click', function(){
        _this.editDatasource(onChange);
      });
      
      sourceWrapper.appendChild(genSource);
      sourceCell.appendChild(sourceWrapper);
      sourceCell.appendChild(editBtn);
      
      // information popup for source
      
      var popOverSettingsSource = {
          placement: 'top',
          container: 'body',
          trigger: 'manual',
          html: true,
          content: function () {
              var publication = _this.publications.get(flow.get('publication'));
              if (publication == null) return '';
              var html = document.getElementById('popover-source-template').innerHTML;
              var template = _.template(html);
              var content = template({publication: publication});
              return content;
          }
      }
      
      this.setupPopover($(sourceWrapper).popover(popOverSettingsSource));
      
      return row;
    },
    
    editFractions: function(flow, items){
      
      var _this = this;
      var modal = document.getElementById('fractions-modal');
      var inner = document.getElementById('fractions-modal-template').innerHTML;
      var template = _.template(inner);
      var html = template({waste: flow.get('waste')});
      modal.innerHTML = html;
      
      var itemSelect = modal.querySelector('select[name="items"]');
      var customOption = document.createElement("option");
      customOption.text = customOption.title = gettext('custom');
      customOption.value = -1;
      customOption.disabled = true;
      itemSelect.appendChild(customOption);
      items.each(function(item){
        var option = document.createElement("option");
        var name = item.get('name');
        item.get('ewc') || item.get('cpa');
        option.title = name;
        option.value = item.id;
        var suffix = item.get('ewc') || item.get('cpa') || '-';
        option.text = '[' + suffix + '] ' + name;
        if (option.text.length > 70) option.text = option.text.substring(0, 70) + '...';
        itemSelect.appendChild(option);
      });
      
      var composition = flow.get('composition') || {};
      itemSelect.value = composition.id || -1;
      // if js doesn't find the id in the select box, it set's index to -1 -> item appears to be custom
      if (itemSelect.selectedIndex < 0) itemSelect.value = -1;
      itemSelect.title = composition.name || '';
      var fractions = composition.fractions || [];
      
      function setCustom(){
        itemSelect.value = -1;
        itemSelect.title = '';
      }
      
      var table = document.getElementById('fractions-edit-table')
      
      function addFractionRow(fraction){
        var row = table.insertRow(-1);
        var fractionsCell = row.insertCell(-1);
        var fInput = document.createElement("input");
        fInput.type = 'number';
        fInput.name = 'fraction';
        fInput.style = 'text-align: right;';
        fInput.max = 100;
        fInput.min = 0;
        fInput.style.float = 'left';
        fractionsCell.appendChild(fInput);
        fInput.value = Math.round(fraction.fraction * 1000) / 10;
        fInput.addEventListener('change', setCustom);
        
        var perDiv = document.createElement('div');
        perDiv.innerHTML = '%';
        perDiv.style.float = 'left';
        perDiv.style.marginLeft = perDiv.style.marginRight = '5px';
        fractionsCell.appendChild(perDiv);
        var matSelect = document.createElement("select");
        matSelect.name = 'material';
        matSelect.style.float = 'left';
        
        _this.materials.each(function(material){
          var option = document.createElement("option");
          var name = material.get('name');
          option.text = name.substring(0, 70);
          if (name.length > 70) option.text += '...';
          option.title =  material.get('name');
          option.value = material.id;
          matSelect.add(option);
        })
        matSelect.value = fraction.material;
        if (matSelect.selectedIndex >= 0)
          matSelect.title = matSelect.options[matSelect.selectedIndex].title;
        fractionsCell.appendChild(matSelect);
        matSelect.addEventListener('change', function(){
          matSelect.title = matSelect.options[matSelect.selectedIndex].title;
          setCustom();
        });
        
        // ToDo: datasource
        row.insertCell(-1)
        
        var removeBtn = document.createElement('button');
        removeBtn.classList.add('btn', 'btn-warning', 'square');
        removeBtn.title = gettext('remove fraction');
        var span = document.createElement('span');
        span.classList.add('glyphicon', 'glyphicon-minus');
        removeBtn.appendChild(span);
        row.insertCell(-1).appendChild(removeBtn);
        removeBtn.addEventListener('click', function(){
          row.parentNode.removeChild(row);
          setCustom();
        });
      }
      
      // put the given fractions into the table
      function setFractions(fractions) {
        _.each(fractions, addFractionRow)
      }
      
      setFractions(fractions);
      
      // on selection of new item render its fractions
      itemSelect.addEventListener('change', function(){
        var item = items.get(itemSelect.value);
        // delete all rows except first one (= header)
        while (table.rows.length > 1) table.deleteRow(1);
        itemSelect.title = item.get('name');
        setFractions(item.get('fractions'));
      });
      
      var addBtn = modal.querySelector('#add-fraction-button');
      addBtn.addEventListener('click', function(){
        addFractionRow( { fraction: 0, material: -1 } )
      });
      
      // fraction confirmed by clicking OK, completely recreate the composition
      var okBtn = modal.querySelector('#confirm-fractions');
      okBtn.addEventListener('click', function(){
        var composition = {};
        var item = items.get(itemSelect.value);
        // no item -> set id to null and name to "custom"
        composition.id = (item) ? item.id : null;
        composition.name = (item) ? item.get('name') : gettext('custom');
        composition.fractions = [];
        for (var i = 1; i < table.rows.length; i++) {
          var row = table.rows[i];
          var fInput = row.querySelector('input[name="fraction"]');
          var matSelect = row.querySelector('select[name="material"]');
          var f = fInput.value / 100;
          var fraction = { 
            'fraction': Number(Math.round(f+'e3')+'e-3'),
            'material': matSelect.value 
          };
          composition.fractions.push(fraction);
        }
        flow.set('composition', composition);
        $(modal).modal('hide');
      })
      
      // finally show the modal after setting it up
      $(modal).modal('show');
    },

    // on click add row button
    addFlowEvent: function(event){
      var buttonId = event.currentTarget.id;
      var tableId;
      var flow;
      var targetIdentifier;
      var isStock = false;
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
        isStock = true;
      }
      this.addFlowRow(tableId, flow, targetIdentifier, isStock);

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
    
    // open modal for setting the datasource
    editDatasource: function(onChange){
      var _this = this;
      this.activeDs = null;
      _.each(this.dsRows, function(row){ row.classList.remove('selected'); });
      this.onDsChange = onChange;
      $('#datasource-modal').modal('show'); 
    },
    
    confirmDatasource: function(){
      this.onDsChange(this.activeDs);
    },
    
    setupDsTable: function(){
      require('libs/jquery.tablesorter.pager');
      $(this.dsTable).tablesorter({
        widgets: ['filter'],
        widgetOptions : {
          filter_placeholder: { search : gettext('Search') + '...' }
        }
      });
      // ToDo: set tablesorter pager if table is empty (atm deactivated in this case, throws errors)
      if ($(this.dsTable).find('tr').length > 1)
        $(this.dsTable).tablesorterPager({container: $("#dspager")});
      
      ////workaround for a bug in tablesorter-pager by triggering
      ////event that pager-selection changed to redraw number of visible rows
      var sel = document.getElementById('dspagesize');
      sel.selectedIndex = 0;
      sel.dispatchEvent(new Event('change'));
    },
    
    refreshDatasources(){
      var _this = this;
      this.publications.fetch({ success: function(){
        // workaround for tablesorter not clearing and adding new rows properly -> destroy the whole thing and setup again
        $(_this.dsTable).trigger("destroy");
        _this.renderDatasources(_this.publications);
        _this.setupDsTable();
      }});
    },
    
    renderDatasources: function(publications){
      var _this = this;
      var table = this.dsTable;
      this.dsRows = [];
      // avoid error message if not initialized with tablesorter yet
      try {
        $.tablesorter.clearTableBody($(table)[0]);
      }
      catch (err) { }
      publications.each(function(publication){
        var row = table.getElementsByTagName('tbody')[0].insertRow(-1);
        row.style.cursor = 'pointer';
        _this.dsRows.push(row);
        row.insertCell(-1).innerHTML = publication.get('title');
        row.insertCell(-1).innerHTML = publication.get('type');
        row.insertCell(-1).innerHTML = publication.get('authors');
        row.insertCell(-1).innerHTML = publication.get('doi');
        var anchor = document.createElement('a');
        var url = publication.get('publication_url');
        anchor.href = url;
        anchor.innerHTML = url;
        anchor.target = '_blank';
        row.insertCell(-1).appendChild(anchor);
        
        // this is supposed to inform tablesorter of a new row, but instead clears the table here, no idea why
        //$(table).trigger('addRows', [$(row), true]);
        
        row.addEventListener('click', function() {
          _.each(_this.dsRows, function(row){ row.classList.remove('selected'); });
          row.classList.add('selected');
          _this.activeDs = publication;
        });
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
          _this.onUpload();
        }).fail(onError);
      }).fail(onError);
    },

    /**
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