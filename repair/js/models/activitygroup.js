define(["backbone", "app-config"],

  function(Backbone, config) {

    var ActivityGroup = Backbone.Model.extend({
      idAttribute: "id",
      tag: "activitygroup",
      urlRoot: function(){
        return config.api.activitygroups.format(this.caseStudyId, this.keyflowId);
      },

      initialize: function (attributes, options) {
        this.caseStudyId = options.caseStudyId;
        this.keyflowId = options.keyflowId;
      },

    });
    return ActivityGroup;
  }
);