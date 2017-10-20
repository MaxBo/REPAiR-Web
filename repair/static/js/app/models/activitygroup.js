define(["backbone"],

  function(Backbone) {

    var ActivityGroup = Backbone.Model.extend({
      idAttribute: "id",
      urlRoot: function(){
        return config.api.activitygroups.format(this.caseStudyID);
      },

      initialize: function (options) {
        this.caseStudyID = options.caseStudyID;
      },

      defaults: {
        id: '',
        name: ''
      },

    });
    return ActivityGroup;
  }
);