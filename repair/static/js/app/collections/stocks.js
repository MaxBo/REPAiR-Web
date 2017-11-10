define(["backbone", "app-config"],

  function(Backbone, config) {
  
    var Stocks = Backbone.Collection.extend({
      url: function(){
        var url = (this.type == 'activity') ? config.api.activityStock:
                  (this.type == 'actor') ? config.api.actorStock:
                  config.api.groupStock;
        return url.format(this.caseStudyId, this.materialId);
      },
      
      initialize: function (options) {
        this.caseStudyId = options.caseStudyId;
        this.materialId = options.materialId;
        this.type = options.type;
      },
    });
    
    return Stocks;
  }
);