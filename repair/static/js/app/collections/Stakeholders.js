define(["backbone","app/models/Stakeholder"],

    function(Backbone, Stakeholder) {

        var Stakeholders = Backbone.Collection.extend({
            url: '/api/stakeholders/',
            model: Stakeholder
        });
        
        return Stakeholders;
    }
);