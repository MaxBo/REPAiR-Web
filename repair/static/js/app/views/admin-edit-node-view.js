define(['backbone'],
  function(Backbone, Sankey, DataTree){
    var EditNodeView = Backbone.View.extend({

      initialize: function(options){
        _.bindAll(this, 'render');
        this.template = options.template;
        this.render();
      },

      render: function(){
        var html = document.getElementById(this.template).innerHTML
        var template = _.template(html);
        this.el.innerHTML = template();
      },

      close: function(){
        this.unbind(); // Unbind all local event bindings
        //this.remove(); // Remove view from DOM
        this.el.innerHTML = ''; //empty the DOM element
      },

    });
    return EditNodeView;
  }
);