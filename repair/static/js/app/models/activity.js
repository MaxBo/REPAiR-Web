define(["backbone"],

  function(Backbone) {

    var Activity = Backbone.Model.extend({
      idAttribute: "id",
      urlRoot: function(){
        if (this.activityGroupCode != null)
          return config.api.activitiesInGroup.format(this.caseStudyId, 
                                              this.activityGroupCode);
        else
          return config.api.activities.format(this.caseStudyId);
      },

      initialize: function (options) {
        this.caseStudyId = options.caseStudyId;
        this.activityGroupCode = options.activityGroupCode;
      },

    });
    return ActivityGroup;
  }
);