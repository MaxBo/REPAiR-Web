define(["backbone"],

    function(Backbone) {

        var Stakeholder = Backbone.Model.extend({
          
            //urlRoot: '/api/stakeholders/',
            idAttribute: "id",
            
            defaults: {
                id: '',
                name: ''
            },

            initialize: function() {
            },
            
        });
        return Stakeholder;
    }
);