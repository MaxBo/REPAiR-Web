define(["backbone", "app-config"],

  function(Backbone, config) {

    var ActivityGroup = Backbone.Model.extend({
      idAttribute: "code",
      urlRoot: function(){
        return config.api.activitygroups.format(this.caseStudyId);
      },

      initialize: function (options) {
        this.caseStudyId = options.caseStudyId;
      },

    });
    return ActivityGroup;
  }
);