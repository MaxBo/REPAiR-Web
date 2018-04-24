define(['views/baseview', 'underscore', 'models/activitygroup', 'models/activity',
    'models/actor', 'collections/flows', 'collections/stocks',
    'collections/products', 'collections/wastes',
    'utils/loader', 'datatables.net', 'datatables.net-buttons/js/buttons.html5.js'],
function(BaseView, _, ActivityGroup, Activity, Actor, Flows, Stocks, Products,
    Wastes, Loader){
/**
*
* @author Christoph Franke
* @name module:views/EditNodeView
* @augments module:views/BaseView
*/

var EditNodeView = BaseView.extend(
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

        // the nace of the model determines the products/wastes of the flows out
        var nace = this.model.get('nace') || 'None';
        // join list of nace codes to comma seperated query param
        if (nace instanceof Array)
            nace = nace.join()

        // fetch inFlows and outFlows with different query parameters
        $.when(
            this.inFlows.fetch({ data: { destination: this.model.id } }),
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
        
        var table = this.el.querySelector('#publications-table');
        this.datatable = $(table).DataTable({
            "columnDefs": [{
                "render": function ( data, type, row ) {
                    var wrapper = document.createElement('a'),
                        anchor = document.createElement('a');
                    wrapper.appendChild(anchor);
                    anchor.href = data;
                    anchor.innerHTML = data;
                    anchor.target = '_blank';
                    return wrapper.innerHTML;
                },
                "targets": 4
            }]
        });
        this.renderDatasources(this.publications);
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
        var addInput = function(attribute, inputType, unit){
            var input = document.createElement("input");
            if (inputType != null)
                input.type = inputType;
            input.value = flow.get(attribute);
            var cell = row.insertCell(-1);
            if (unit){
                var div = document.createElement('div'),
                    wrapper = document.createElement('div');
                div.innerHTML = unit
                wrapper.appendChild(input);
                wrapper.appendChild(div);
                wrapper.style.whiteSpace = "nowrap";
                input.style.float = 'left';
                // need space for units
                input.style.maxWidth = '70%'; 
                cell.appendChild(wrapper);
            }

            else cell.appendChild(input);

            input.addEventListener('change', function() {
                flow.set(attribute, input.value);
            });
            return input;
        };

        var amount = addInput('amount', 'number', gettext('t/year'));
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
        editFractionsBtn.innerHTML = gettext('Composition');

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
                // ToDo: removce this after collection/model rework
                origin.caseStudyId = _this.caseStudyId;
                origin.keyflowId = _this.keyflowId;
                origin.fetch({success: function(){
                    var nace = origin.get('nace') || 'None';
                    var loader = new Loader(document.getElementById('flows-edit'),
                        {disable: true});
                    var items = (flow.get('waste') == 'true') ? new Wastes([], options): new Products([], options);
                    items.getFirstPage({ data: { nace: nace } }).then( 
                        function(){ _this.editFractions(flow, items); loader.remove(); }
                    )
                }})
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

        var sourceCell = row.insertCell(-1);
        // prevent breaking 
        sourceCell.setAttribute("style", "white-space: nowrap");
        this.addPublicationInput(sourceCell, flow.get('publication'), 
            function(id){ flow.set('publication', id) })

        return row;
    },

    /*
        * add input for publication to given cell, value is set to currentId
        * onChange(publicationId) is called when publication is confirmed by user
        */
    addPublicationInput: function(cell, currentId, onChange, container){
        var _this = this;
        var sourceWrapper = document.createElement('div');
        sourceWrapper.style.float = 'left';
        sourceWrapper.style.maxWidth = '80%';
        var sourceInput = document.createElement('input');
        sourceInput.name = 'publication';
        sourceInput.style.maxWidth = '90%';
        if (currentId){
            var publication = this.publications.get(currentId)
            var title = publication.get('title');
            sourceInput.value = title;
            sourceInput.setAttribute('data-publication-id', currentId)
        }
        sourceInput.disabled = true;
        sourceInput.style.cursor = 'pointer';
        var editBtn = document.createElement('button');
        var pencil = document.createElement('span');
        editBtn.classList.add('btn', 'btn-primary', 'square');
        editBtn.appendChild(pencil);
        editBtn.title = gettext('Edit data source');
        pencil.classList.add('glyphicon', 'glyphicon-pencil');

        function onConfirm(publication){
            if (publication != null){
                var title = publication.get('title');
                sourceInput.value = title;
                sourceInput.setAttribute('data-publication-id', publication.id)
                onChange(publication.id)
                sourceInput.dispatchEvent(new Event('change'));
            }
        };
        editBtn.addEventListener('click', function(){
            _this.editDatasource(onConfirm);
        });

        sourceWrapper.appendChild(sourceInput);
        cell.appendChild(sourceWrapper);
        cell.appendChild(editBtn);

        // information popup for source

        var popOverSettingsSource = {
            placement: 'left',
            container: container || 'body',
            trigger: 'manual',
            html: true,
            content: function () {
                var pubId = sourceInput.getAttribute('data-publication-id');
                var publication = _this.publications.get(pubId);
                if (publication == null) return '';
                var html = document.getElementById('popover-source-template').innerHTML;
                var template = _.template(html);
                var content = template({ publication: publication });
                return content;
            }
        }

        this.setupPopover($(sourceWrapper).popover(popOverSettingsSource));
    },

    /*
        * open modal dialog for editing the fractions of a flow 
        * items are the available products/wastes the user can select from
        */
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

        // add a row to the fractions table with inputs and event listeners
        function addFractionRow(fraction){

            // input for fraction percentage
            var row = table.insertRow(-1);
            var fractionsCell = row.insertCell(-1),
                fractionWrapper = document.createElement("div");
            fractionsCell.appendChild(fractionWrapper);
            fractionWrapper.style.whiteSpace = 'nowrap';
            var fInput = document.createElement("input");
            fInput.type = 'number';
            fInput.name = 'fraction';
            fInput.style = 'text-align: right;';
            fInput.max = 100;
            fInput.min = 0;
            fInput.style.maxWidth = '80%';
            fInput.style.float = 'left';
            fractionWrapper.appendChild(fInput);
            fInput.value = Math.round(fraction.fraction * 1000) / 10;
            fInput.addEventListener('change', setCustom);

            var perDiv = document.createElement('div');
            perDiv.innerHTML = '%';
            perDiv.style.marginLeft = perDiv.style.marginRight = '5px';
            fractionWrapper.appendChild(perDiv);

            // select material
            var matSelect = document.createElement('div');
            matSelect.classList.add('materialSelect');
            matSelect.setAttribute('data-material-id', fraction.material);
            _this.hierarchicalSelect(_this.materials, matSelect, {
                onSelect: function(model){
                    var matId = (model) ? model.id : '';
                    matSelect.setAttribute('data-material-id', matId);
                    setCustom();
                },
                width: 300,
                selected: fraction.material,
                defaultOption: gettext('Select a material')
            });
            matSelect.style.float = 'left';
            row.insertCell(-1).appendChild(matSelect);
            
            var avoidCheck = document.createElement('input');
            avoidCheck.type = 'checkbox';
            avoidCheck.name = 'avoidable';
            console.log(fraction)
            avoidCheck.checked = fraction.avoidable;
            row.insertCell(-1).appendChild(avoidCheck);
        
            var sourceCell = row.insertCell(-1);
            sourceCell.setAttribute("style", "white-space: nowrap");
            _this.addPublicationInput(sourceCell, fraction.publication, function(id){
                setCustom();
            }, '#fractions-modal')

            // button to remove the row
            var removeBtn = document.createElement('button');
            removeBtn.classList.add('btn', 'btn-warning', 'square');
            removeBtn.title = gettext('remove fraction');
            removeBtn.style.float = 'right';
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

        // init with fractions of current composition
        setFractions(fractions);

        // on selection of new item render its fractions
        itemSelect.addEventListener('change', function(){
            var item = items.get(itemSelect.value);
            // delete all rows except first one (= header)
            while (table.rows.length > 1) table.deleteRow(1);
            itemSelect.title = item.get('name');
            setFractions(item.get('fractions'));
        });

        // button for adding the fraction
        var addBtn = modal.querySelector('#add-fraction-button');
        addBtn.addEventListener('click', function(){
            addFractionRow( { fraction: 0, material: '', publication: null } );
            setCustom();
        });

        // fraction confirmed by clicking OK, completely recreate the composition
        var okBtn = modal.querySelector('#confirm-fractions');

        okBtn.addEventListener('click', function(){

            var fractionInputs = modal.querySelectorAll('input[name="fraction"]');
            var sum = 0;

            var errorMsg;

            // sum test
            for (i = 0; i < fractionInputs.length; i++) {
                sum += parseFloat(fractionInputs[i].value); // strangely the input returns a text (though its type is number)
            }
            sum = Math.round(sum);

            if (sum != 100){
                var errorMsg = gettext("The fractions have to sum up to 100!") + ' (' + gettext('current sum') + ': ' + sum + ')';
            } else {
                // if sum test is passed check materials
                var matSelects = modal.querySelectorAll('.materialSelect');
                var matIds = []
                for (i = 0; i < matSelects.length; i++) {
                    var matId = matSelects[i].getAttribute('data-material-id');
                    if (!matId) {
                        errorMsg = gettext('All materials have to be set!');
                        break;
                    }
                    if (matIds.includes(matId)){
                        errorMsg = gettext('Multiple fractions with the same material are not allowed!');
                        break;
                    }
                    matIds.push(matId);
                }
            }

            if (errorMsg){
                _this.alert(errorMsg, gettext('Error'));
                return;
            }

            // set the compositions after completing checks
            var composition = {};
            var item = items.get(itemSelect.value);
            // no item -> set id to null and name to "custom"
            composition.id = (item) ? item.id : null;
            composition.name = (item) ? item.get('name') : gettext('custom');
            composition.fractions = [];
            for (var i = 1; i < table.rows.length; i++) {
                var row = table.rows[i];
                var fInput = row.querySelector('input[name="fraction"]');
                var matSelect = row.querySelector('.materialSelect');
                var avoidCheck = row.querySelector('input[name="avoidable"]')
                var pubInput = row.querySelector('input[name="publication"]');
                var f = fInput.value / 100;
                var fraction = { 
                    'fraction': Number(Math.round(f+'e3')+'e-3'),
                    'material': matSelect.getAttribute('data-material-id'),
                    'publication': pubInput.getAttribute('data-publication-id'),
                    'avoidable': avoidCheck.checked
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
            url: this.model.get('website'),
            year: this.model.get('year'),
            employees: this.model.get('employees'),
            turnover: this.model.get('turnover')
        });
    },

    // open modal for setting the datasource
    editDatasource: function(onConfirm){
        var _this = this;
        this.activePublication = null;
        _.each(this.dsRows, function(row){ row.classList.remove('selected'); });
        this.onPubConfirmed = onConfirm;
        $('#datasource-modal').modal('show'); 
    },

    confirmDatasource: function(){
        this.onPubConfirmed(this.activePublication);
    },

    /*
        * refresh the table of publications
        */
    refreshDatasources(){
        var _this = this;
        this.publications.fetch({ success: function(){
            _this.renderDatasources(_this.publications);
        }});
    },

    /*
        * prerender the table for publications inside a modal
        */
    renderDatasources: function(publications){
        var _this = this;
        this.datatable.clear();
        
        this.dsRows = [];
        publications.each(function(publication){
            var dataRow = _this.datatable.row.add([
                    publication.get('title'),
                    publication.get('type'),
                    publication.get('authors'),
                    publication.get('doi'),
                    publication.get('publication_url')
                ]).draw(),
                row = dataRow.node();
            row.style.cursor = 'pointer';
            _this.dsRows.push(row);

            row.addEventListener('click', function() {
                _.each(_this.dsRows, function(row){ row.classList.remove('selected'); });
                row.classList.add('selected');
                _this.activePublication = publication;
            });
        });
    },
    
    flowRepr: function(flow){
        var origin = this.model.collection.get(flow.get('origin')),
            origName = origin.get('name'),
            dest = this.model.collection.get(flow.get('destination'));
            
        if (!dest) return origName + ' ' + gettext('Stock');
        return origName + ' -> ' + dest.get('name');
    },
    
    getChangedModels: function(){
        var changed = [];
        // update existing models
        var checkUpdate = function(model){
            if (model.markedForDeletion || model.changedAttributes() != false)
                changed.push(model);
        };
        this.inFlows.each(checkUpdate);
        this.outFlows.each(checkUpdate);
        this.stocks.each(checkUpdate);

        // save added flows only, when they are not marked for deletion
        var checkCreate = function(model){
            if (!model.markedForDeletion && Object.keys(model.attributes).length > 0) // sometimes empty models sneak in, not sure why
                changed.push(model);
        }
        this.newInFlows.each(checkCreate);
        this.newOutFlows.each(checkCreate);
        this.newStocks.each(checkCreate);
        
        return changed;
    },
    
    hasChanged: function(){
        return (this.getChangedModels().length > 0)
    },

    uploadChanges: function(){
        var _this = this;
        var models = this.getChangedModels();

        var loader = new Loader(document.getElementById('flows-edit'),
            {disable: true});

        var onError = function(model, response){
            var name = _this.flowRepr(model);
            _this.onError(response, name); 
            loader.remove();
        };

        // upload the models recursively (starting at index it)
        function uploadModel(models, it){
            // end recursion if no elements are left and call the passed success method
            if (it >= models.length) {
                loader.remove();
                _this.onUpload();
                return;
            };
            var model = models[it];
            // upload or destroy current model and upload next model recursively on success
            var params = {
                success: function(){ uploadModel(models, it+1) },
                error: function(model, response){ onError(model, response) }
            }
            if (model.markedForDeletion)
                model.destroy(params);
            else {
                model.save(null, params);
            }
        };

        // start recursion at index 0
        uploadModel(models, 0);
    },

});
return EditNodeView;
}
);