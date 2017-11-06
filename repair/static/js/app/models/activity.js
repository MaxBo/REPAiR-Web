define(["backbone", "app-config"],

  function(Backbone, config) {

    var Activity = Backbone.Model.extend({
      idAttribute: "url",
      tag: "activity",
      urlRoot: function(){
        // if a group is given, take the route that retrieves all activities 
        // of the group
        if (this.activityGroupCode != null)
          return config.api.activitiesInGroup.format(this.caseStudyId, 
                                                     this.activityGroupCode);
        // if no group is given, get all activities in the casestudy
        else
          return config.api.activities.format(this.caseStudyId);
      },

      initialize: function (options) {
        this.caseStudyId = options.caseStudyId;
        this.activityGroupCode = options.activityGroupCode;
      },

    });
    return Activity;
  }
);