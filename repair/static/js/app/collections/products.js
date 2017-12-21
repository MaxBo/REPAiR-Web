define(["backbone", "app-config"],

  function(Backbone, config) {

    var Products = Backbone.Collection.extend({
      url: function(){
        return config.api.products.format(this.caseStudyId, this.keyflowId);
      },
      
      initialize: function (attrs, options) {
        this.caseStudyId = options.caseStudyId;
        this.keyflowId = options.keyflowId;
      }
    });

    return Products;
  }
);