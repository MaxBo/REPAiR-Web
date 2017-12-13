define(["backbone", "app-config"],

  function(Backbone, config) {

    var Activity = Backbone.Model.extend({
      idAttribute: "id",
      tag: "activity",
      urlRoot: function(){
        // if a group is given, take the route that retrieves all activities 
        // of the group
        if (this.activityGroupCode != null)
          return config.api.activitiesInGroup.format(this.caseStudyId, 
                                                     this.keyflowId,
                                                     this.activityGroupCode);
        // if no group is given, get all activities in the casestudy
        else
          return config.api.activities.format(this.caseStudyId, this.keyflowId);
      },

      initialize: function (attributes, options) {
        this.caseStudyId = options.caseStudyId;
        this.activityGroupCode = options.activityGroupCode;
        this.keyflowId = options.keyflowId;
      },

    });
    return Activity;
  }
);