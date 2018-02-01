define(['backbone', 'underscore', 'utils/loader'],

function(Backbone, _, Products, Loader){
  var EditMaterialsView = Backbone.View.extend({

    /*
      * view-constructor
      */
    initialize: function(options){
      _.bindAll(this, 'render');
      var _this = this;
      
      this.template = options.template;
      this.caseStudy = options.caseStudy;
      var keyflowId = this.model.id,
          caseStudyId = this.caseStudy.id;
      
      this.materials = options.materials;
      
      this.render();
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
      this.el.innerHTML = template({casestudy: this.caseStudy.get('properties').name,
                                    keyflow: this.model.get('name')});
       
      this.renderDataTree();

    },
    
    
    /*
     * render the hierarchic tree of materials
     */
    renderDataTree: function(){
    
      var _this = this;
      var dataDict = {};
      
      function treeify(list) {
        var treeList = [];
        var lookup = {};
        list.forEach(function(item) {
          lookup[item['id']] = item;
          item['nodes'] = [];
        });
        list.forEach(function(item) {
          if (item['parent'] != null) {
              lookup[item['parent']]['nodes'].push(item);
          } else treeList.push(item);
        });
        return treeList;
      };
    
      var materialList = [];
      this.materials.each(function(material){
        var mat = { 
          id: material.id, 
          parent: material.get('parent'),
          text: material.get('name'),
          model: material,
          state: {checked: false}
        };
        materialList.push(mat);
      });
    
      var materialTree = treeify(materialList);
      var divid = '#material-tree';
      require('libs/bootstrap-treeview.min');
      $(divid).treeview({data: materialTree, showTags: true,
                         selectedBackColor: '#aad400',
                         //onNodeSelected: onClick,
                         //showCheckbox: true
                         });
      $(divid).treeview('collapseAll', {silent: true});
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
  return EditMaterialsView;
}
);