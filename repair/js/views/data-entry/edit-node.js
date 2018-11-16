define(['views/common/baseview', 'underscore',
        'collections/gdsecollection', 'models/gdsemodel',
        'app-config', 'datatables.net',
        'datatables.net-buttons/js/buttons.html5.js','bootstrap-select'],
function(BaseView, _, GDSECollection, GDSEModel, config){
/**
*
* @author Christoph Franke
* @name module:views/EditNodeView
* @augments module:views/BaseView
*/

function toggleBtnClass(button, cls){
    button.classList.remove('btn-primary', 'btn-warning', 'btn-danger');
    button.classList.add(cls);
};

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
    * @param {module:collections/Materials} options.materials        the available materials
    * @param {module:collections/Publications} options.publications  the available publications
    * @param {module:views/EditNodeView~onUpload=} options.onUpload  called after successfully uploading the flows
    *
    * @constructs
    * @see http://backbonejs.org/#View
    */
    initialize: function(options){
        EditNodeView.__super__.initialize.apply(this, [options]);
        this.template = options.template;
        this.keyflowId = options.keyflowId;
        this.caseStudyId = options.caseStudyId;
        this.materials = options.materials;
        this.publications = options.publications;
        this.showNodeInfo = (options.showNodeInfo == false) ? false: true;

        this.onUpload = options.onUpload;
        var apiTag = options.apiTag || this.model.apiTag;
        this.flowTag = (apiTag == 'actors') ? 'actorToActor':
                       (apiTag == 'activities') ? 'activityToActivity':
                       'groupToGroup';
        this.stockTag = (apiTag == 'actors') ? 'actorStock':
                        (apiTag == 'activities') ? 'activityStock':
                        'groupStock';

        this.inFlows = new GDSECollection([], {
            apiTag: this.flowTag,
            apiIds: [ this.caseStudyId, this.keyflowId ]
        });
        this.outFlows = new GDSECollection([], {
            apiTag: this.flowTag,
            apiIds: [ this.caseStudyId, this.keyflowId ]
        });
        this.stocks = new GDSECollection([], {
            apiTag: this.stockTag,
            apiIds: [ this.caseStudyId, this.keyflowId ]
        });

        this.newInFlows = new GDSECollection([], {
            apiTag: this.flowTag,
            apiIds: [ this.caseStudyId, this.keyflowId ]
        });
        this.newOutFlows = new GDSECollection([], {
            apiTag: this.flowTag,
            apiIds: [ this.caseStudyId, this.keyflowId ]
        });
        this.newStocks = new GDSECollection([], {
            apiTag: this.stockTag,
            apiIds: [ this.caseStudyId, this.keyflowId ]
        });

        this.outProducts = new GDSECollection([], {
            apiTag: 'products'
        });
        this.outWastes = new GDSECollection([], {
            apiTag: 'wastes'
        });

        var _this = this;

        this.loader.activate();

        // the nace of the model determines the products/wastes of the flows out
        var nace = this.model.get('nace') || 'None';
        // join list of nace codes to comma seperated query param
        if (nace instanceof Array)
            nace = nace.join();

        var promises = [
            this.inFlows.fetch({ data: { destination: this.model.id } }),
            this.outFlows.fetch({ data: { origin: this.model.id } }),
            this.stocks.fetch({ data: { origin: this.model.id } }),
            this.outProducts.getFirstPage({ data: { nace: nace } }),
            this.outWastes.getFirstPage({ data: { nace: nace } })
        ]

        Promise.all(promises).then(function() {
            _this.loader.deactivate();
            _this.render();
        })
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'click #upload-flows-button': 'uploadChanges',
        'click #add-input-button, #add-output-button, #add-stock-button': 'addFlowEvent',
        'click #confirm-datasource': 'confirmDatasource',
        'click #refresh-publications-button': 'refreshDatasources',
        'click #flow-nodes-modal .confirm': 'confirmNodeSelection'
    },

    /*
    * render the view
    */
    render: function(){
        var _this = this;
        var html = document.getElementById(this.template).innerHTML
        var template = _.template(html);
        this.el.innerHTML = template({name: this.model.get('name')});

        var content = this.nodePopoverContent(this.model);

        if (this.showNodeInfo){
            var popOverSettings = {
                placement: 'right',
                container: 'body',
                html: true,
                content: content
            }

            this.setupPopover($('#node-info-popover').popover(popOverSettings));
        }
        else
            this.el.querySelector('#node-info-popover').querySelector('.glyphicon').style.display = 'none';

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
        this.setupNodeTable();
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

        var table = this.el.querySelector('#' + tableId),
            row = table.insertRow(-1),
            editFractionsBtn = document.createElement('button'),
            typeSelect = document.createElement("select");
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
            var targetCell = row.insertCell(-1),
                targetId = flow.get(targetIdentifier),
                target,
                targetButton = document.createElement('button');

            targetCell.appendChild(targetButton);
            targetButton.name = 'target';
            targetButton.style.width = '100%';
            targetButton.style.overflow = 'hidden';
            targetButton.style.textOverflow = 'ellipsis';
            targetButton.style.color = 'black';
            targetButton.style.maxWidth = '200px';
            targetButton.classList.add('btn', 'inverted', 'square', 'btn-danger');
            targetButton.innerHTML = '-';

            function setTarget(id){
                target = new GDSEModel({ id : id }, { url: _this.model.urlRoot() });
                target.fetch({
                    success: function(){
                        toggleBtnClass(targetButton, 'btn-primary');
                        targetButton.innerHTML = target.get('name');

                    }, error: this.onError
                })
            }

            if (targetId) setTarget(targetId);

            var popOverSettings = {
                placement: 'right',
                container: 'body',
                html: true,
                title: '',
                content: function(){
                    return _this.nodePopoverContent(target);
                }
            }

            this.setupPopover($(targetButton).popover(popOverSettings));

            targetButton.addEventListener('click', function(){
                //_this.selectActor(onConfirm);
                _this.onConfirmNode = function(id, name){
                    flow.set(targetIdentifier, id);
                    setTarget(id);
                }
                $('#flow-nodes-modal').modal('show');
            })

        };

        var itemWrapper = document.createElement("span");
        // prevent breaking
        itemWrapper.setAttribute("style", "white-space: nowrap");
        row.insertCell(-1).appendChild(itemWrapper);

        // input for product
        var wasteOption = document.createElement("option")
        wasteOption.value = 'true'; wasteOption.text = gettext('Waste');
        typeSelect.appendChild(wasteOption);
        var productOption = document.createElement("option")
        productOption.value = 'false'; productOption.text = gettext('Product');
        typeSelect.appendChild(productOption);
        typeSelect.value = flow.get('waste');

        typeSelect.addEventListener('change', function() {
            var isWaste = typeSelect.value
            flow.set('waste', isWaste);
            // remove the composition on type change
            flow.set('composition', null);
        });

        itemWrapper.appendChild(typeSelect);
        var pencil = document.createElement('span'),
            btnClass = (flow.get('composition')) ? 'btn-primary' : 'btn-danger';

        editFractionsBtn.classList.add('btn', 'square');
        toggleBtnClass(editFractionsBtn, btnClass);
        editFractionsBtn.appendChild(pencil);
        editFractionsBtn.innerHTML = gettext('Composition');

        itemWrapper.appendChild(editFractionsBtn);

        editFractionsBtn.addEventListener('click', function(){
            if (flow.get('waste') == null) return;
            // the nace of this node determines the items for stocks and outputs
            if (targetIdentifier == 'destination' || isStock == true){
                var items = (flow.get('waste') == 'true') ? _this.outWastes : _this.outProducts;
                _this.editFractions(flow, items, editFractionsBtn);
            }
            // take nace of origin node in case of inputs
            else {
                var origin = target;
                if (origin == null) return;
                var options = {
                    state: {
                        pageSize: 1000000,
                        firstPage: 1,
                        currentPage: 1
                    }
                };
                var nace = origin.get('nace') || 'None';
                _this.loader.activate();
                var apiTag = (flow.get('waste') == 'true') ? 'wastes': 'products',
                    items = new GDSECollection([], { apiTag: apiTag });
                items.getFirstPage({ data: { nace: nace } }).then(
                    function(){
                        _this.loader.deactivate();
                        _this.editFractions(flow, items, editFractionsBtn);
                    }
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

        // datasource of flow

        var sourceCell = row.insertCell(-1);
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
        var sourceButton = document.createElement('button');
        sourceButton.name = 'publication';
        sourceButton.style.width = '100%';
        sourceButton.style.overflow = 'hidden';
        sourceButton.style.textOverflow = 'ellipsis';
        sourceButton.style.color = 'black';
        sourceButton.style.maxWidth = '200px';
        var btnClass = (currentId) ? 'btn-primary': 'btn-warning';
        sourceButton.classList.add('btn', 'inverted', 'square', btnClass);
        if (currentId){
            var publication = this.publications.get(currentId)
            var title = publication.get('title');
            sourceButton.innerHTML = title;
            sourceButton.setAttribute('data-publication-id', currentId)
        }
        else sourceButton.innerHTML = '-';

        function onConfirm(publication){
            if (publication != null){
                var title = publication.get('title');
                sourceButton.value = title;
                sourceButton.innerHTML = title;
                sourceButton.setAttribute('data-publication-id', publication.id)
                onChange(publication.id);
                toggleBtnClass(sourceButton, 'btn-primary');
            }
            else {
                sourceButton.innerHTML = '-';
                toggleBtnClass(sourceButton, 'btn-warning');
            }
        };
        sourceButton.addEventListener('click', function(){
            _this.editDatasource(onConfirm);
        });

        cell.appendChild(sourceButton);

        // information popup for source

        var popOverSettingsSource = {
            placement: 'left',
            container: container || 'body',
            html: true,
            content: function () {
                var pubId = sourceButton.getAttribute('data-publication-id'),
                    publication = _this.publications.get(pubId);
                if (publication == null) return '';
                var html = document.getElementById('popover-source-template').innerHTML,
                    template = _.template(html),
                    content = template({ publication: publication });
                return content;
            }
        }

        this.setupPopover($(sourceButton).popover(popOverSettingsSource));
    },

    /*
    * open modal dialog for editing the fractions of a flow
    * items are the available products/wastes the user can select from
    */
    editFractions: function(flow, items, button){

        var _this = this,
            modal = document.getElementById('fractions-modal'),
            inner = document.getElementById('fractions-modal-template').innerHTML,
            template = _.template(inner),
            html = template({waste: flow.get('waste')});
        modal.innerHTML = html;

        var itemSelect = modal.querySelector('select[name="items"]'),
            customOption = document.createElement("option");
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
            row.setAttribute('data-id', fraction.id || null);
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
            fInput.style.minWidth = '100px';
            fInput.style.maxWidth = '80%';
            fInput.style.float = 'left';
            fractionWrapper.appendChild(fInput);
            fInput.value = Math.round(fraction.fraction * 10000000) / 100000;
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
            addFractionRow( { fraction: 0, material: '', publication: null, id: null } );
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
                for (i = 0; i < matSelects.length; i++) {
                    var matId = matSelects[i].getAttribute('data-material-id');
                    if (!matId) {
                        errorMsg = gettext('All materials have to be set!');
                        break;
                    }
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
                    fInput = row.querySelector('input[name="fraction"]'),
                    matSelect = row.querySelector('.materialSelect'),
                    avoidCheck = row.querySelector('input[name="avoidable"]'),
                    pubInput = row.querySelector('button[name="publication"]'),
                    f = fInput.value / 100,
                    id = row.getAttribute('data-id');
                if (id == "null") id = null;
                var fraction = {
                    'id': id,
                    'fraction': Number(Math.round(f+'e5')+'e-5'),
                    'material': matSelect.getAttribute('data-material-id'),
                    'publication': pubInput.getAttribute('data-publication-id'),
                    'avoidable': avoidCheck.checked
                };
                composition.fractions.push(fraction);
            }
            flow.set('composition', composition);
            toggleBtnClass(button, 'btn-primary');
            //flow.fractionsChanged = true;
            $(modal).modal('hide');
        })

        // finally show the modal after setting it up
        $(modal).modal('show');
    },

    // on click add row button
    addFlowEvent: function(event){
        var _this = this,
            buttonId = event.currentTarget.id,
            tableId, flow, targetIdentifier,
            isStock = false;
        if (buttonId == 'add-input-button'){
            tableId = 'input-table';
            flow = this.newInFlows.add({});
            targetIdentifier = 'origin';
            flow = this.newOutFlows.add({
                'amount': 0,
                'origin': null,
                'destination': this.model.id,
                'quality': null,
                'waste': false
            });
        }
        else if (buttonId == 'add-output-button'){
            tableId = 'output-table';
            targetIdentifier = 'destination';
            flow = this.newOutFlows.add({
                'amount': 0,
                'origin': this.model.id,
                'destination': null,
                'quality': null,
                'waste': false
            });
        }
        else if (buttonId == 'add-stock-button'){
            tableId = 'stock-table';
            targetIdentifier = 'origin';
            flow = this.newStocks.add({
                'amount': 0,
                'origin': this.model.id,
                'quality': null,
                'waste': false
            });
            isStock = true;
        }
        flow.set('description', '');
        _this.addFlowRow(tableId, flow, targetIdentifier, isStock);

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

    nodePopoverContent: function(model){
        if (!model) return '-';
        var templateId = (this.flowType == 'activitygroup') ? 'group-attributes-template' :
                         (this.flowType == 'activity') ? 'activity-attributes-template' :
                         'actor-attributes-template';
        var html = document.getElementById(templateId).innerHTML,
            template = _.template(html);
        return template({
            model: model
        });
    },

    setupNodeTable: function(){
        var _this = this;
        var columns = [
            {data: 'id', title: 'ID', visible: false},
            {data: 'name', title: gettext('Name')}
        ];
        if (this.model.tag == 'activity')
            columns = columns.concat([
                {data: 'activitygroup_name', title: gettext('Activity Group'), name: 'activitygroup__name'},
                {data: 'nace', title: gettext('Nace Code'), name: 'nace'},
            ]);
        if (this.model.tag == 'actor')
            columns = columns.concat([
                {data: 'activity_name', title: gettext('Activity'), name: 'activity__name'},
                {data: 'activitygroup_name', title: gettext('Activity Group'), name: 'activity__activitygroup__name'},
                {data: 'city', title: gettext('City'), name: 'administrative_location.city'},
                {data: 'address', title: gettext('Address'), name: 'administrative_location.address'},
            ]);
        var table = this.el.querySelector('#flow-nodes-modal table');
        this.nodeDatatable = $(table).DataTable({
            serverSide: true,
            ajax: this.model.urlRoot() + "?format=datatables",
            columns: columns,
            rowId: 'id'
        });
        var body = table.querySelector('tbody');
        $(body).on( 'click', 'tr', function () {
            if ( $(this).hasClass('selected') ) {
                $(this).removeClass('selected');
            }
            else {
                _this.nodeDatatable.$('tr.selected').removeClass('selected');
                $(this).addClass('selected');
            }
        } );
        // add individual search fields for all columns
        if (this.model.tag != 'activitygroup'){
            $(table).append('<tfoot><tr></tr></tfoot>');
            var footer = $('tfoot tr', table);
            var delay = (function(){
                var timer = 0;
                return function(callback, ms){
                    clearTimeout (timer);
                    timer = setTimeout(callback, ms);
                };
            })();
            this.nodeDatatable.columns().every( function () {
                var column = this;
                if (column.visible()){
                    var searchInput = document.createElement('input'),
                        th = document.createElement('th');
                    searchInput.placeholder = gettext('Search');
                    th.appendChild(searchInput);
                    searchInput.name = columns[column.index()].data;
                    searchInput.style.width = '100%';
                    searchInput.autocomplete = "off";
                    footer.append(th);
                    $(searchInput).on( 'keyup change', function () {
                        var input = this;
                        if ( column.search() !== input.value ) {
                            delay(function(){
                                column.search(input.value).draw();
                            }, 400 );
                        }
                    });
                }
            });
        }
    },

    confirmNodeSelection: function(){
        var selected = this.nodeDatatable.row('.selected');
        this.nodeDatatable.$('tr.selected').removeClass('selected');
        if (!selected) return;
        var data = selected.data();
        this.onConfirmNode(data.id, data.name);
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

    getDefaultComposition: function(model, onSuccess){
        // activity groups have no default
        if(model == null || model.tag == 'activitygroup'){
            onSuccess(null);
            return;
        }

        model.fetch({success: function(){
            var nace = model.get('nace') || 'None';
            var items = new GDSECollection([], { apiTag: 'products' });
            items.getFirstPage({ data: { nace: nace } }).then(
                function(){
                    var item = (items.length > 0) ? items.first() : null;
                    onSuccess(item);
                }
            )
        }})
    },

    uploadChanges: function(){
        var _this = this;
        var models = this.getChangedModels();

        this.loader.activate();

        var onError = function(model, response){
            _this.onError(response);
            _this.loader.deactivate();
        };

        // upload the models recursively (starting at index it)
        function uploadModel(models, it){
            // end recursion if no elements are left and call the passed success method
            if (it >= models.length) {
                _this.loader.deactivate();
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
