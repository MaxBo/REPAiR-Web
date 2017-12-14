define(['backbone', 'app/collections/products', 
        'tablesorter-pager', 'app/loader'],

function(Backbone, Products){
  var EditActorsView = Backbone.View.extend({

    /*
      * view-constructor
      */
    initialize: function(options){
      _.bindAll(this, 'render');
      var _this = this;
      
      this.template = options.template;
      var keyflowId = this.model.id,
          caseStudyId = this.model.get('casestudy');
      
      this.products = new Products([], {caseStudyId: caseStudyId, keyflowId: keyflowId});
      this.caseStudy = options.caseStudy;
      this.materials = options.materials;
      this.onUpload = options.onUpload;
      
      var loader = new Loader(this.el);
        
      $.when(this.products.fetch()).then(function() {
          //loader.remove();
          _this.render();
      });
    },

    /*
      * dom events (managed by jquery)
      */
    events: {
    },

    /*
      * render the view
      */
    render: function(){
      var _this = this;
      var html = document.getElementById(this.template).innerHTML
      var template = _.template(html);
      this.el.innerHTML = template({casestudy: this.caseStudy.get('name'),
                                    keyflow: this.model.get('name')});

      this.table = this.el.querySelector('#products-table');

      //// render inFlows
      this.products.each(function(product){_this.addProductRow(product)}); // you have to define function instead of passing this.addActorRow, else scope is wrong
      $(this.table).tablesorter({
        headers:{
          0: {sorter: false},
          1: {sorter: false},
          2: {sorter: false},
        },
        widgets: ['zebra']
      });
    },
    
    addProductRow: function(product){
      var _this = this;

      var row = this.table.getElementsByTagName('tbody')[0].insertRow(-1);

      var input = document.createElement("input");
      input.style.width = '100%';
      input.value = product.get('name');
      row.insertCell(-1).appendChild(input);
      input.addEventListener('change', function() {
        product.set('name', input.value);
        input.classList.add('changed');
      });
      
      var fractionTable = document.createElement("table");
      fractionTable.classList.add('sub-table');
      row.insertCell(-1).appendChild(fractionTable);
      var fractions = product.get('fractions');
      _.each(fractions, function(fraction){
        var fRow = fractionTable.insertRow(-1);
        var fInput = document.createElement("input");
        fInput.type = 'number';
        fInput.style = 'text-align: right;';
        fInput.max = 100;
        fInput.min = 0;
        fRow.insertCell(-1).appendChild(fInput);
        fInput.value = fraction.fraction * 100;
        fRow.insertCell(-1).innerHTML = '%';
        var matSelect = document.createElement("select");
        var ids = [];
        var targetId = fraction.material;
        _this.materials.each(function(material){
          var option = document.createElement("option");
          option.text = material.get('name');
          option.value = material.id;
          matSelect.add(option);
          ids.push(material.id);
        })
        var idx = ids.indexOf(targetId);
        matSelect.selectedIndex = idx.toString();
        fRow.insertCell(-1).appendChild(matSelect);
      });

      // "default" checkbox

      var checkbox = document.createElement("input");
      checkbox.type = 'checkbox';
      var isDefault = product.get('default')
      checkbox.checked = isDefault;
      row.insertCell(-1).appendChild(checkbox);

      checkbox.addEventListener('change', function() {
        product.set('default', checkbox.checked);
      });
      
      
      return row;
    },

    // add row when button is clicked
    addProductEvent: function(event){
      var buttonId = event.currentTarget.id;
      var tableId;
      
      this.products.add(product);
      var row = this.addProductRow(product);
      // let tablesorter know, that there is a new row
      $('table').trigger('addRows', [$(row)]);
      // workaround for going to last page by emulating click
      document.getElementById('goto-last-page').click();
    },

    uploadChanges: function(){

      var _this = this;

      var modelsToSave = [];

      var update = function(model){
        if (model.changedAttributes() != false && Object.keys(model.attributes).length > 0){
          modelsToSave.push(model);
        }
      };
      this.products.each(update);
      //this.adminLocations.each(update);

      // chain save and destroy operations
      var saveComplete = _.invoke(modelsToSave, 'save');

      var loader = new Loader(document.getElementById('flows-edit'),
        {disable: true});
      var onError = function(response){
        alert(response.responseText); 
        loader.remove();
      };
      $.when.apply($, saveComplete).done(function(){
        loader.remove();
        console.log('upload complete');
        _this.onUpload();
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
  return EditActorsView;
}
);