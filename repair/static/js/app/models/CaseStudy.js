define(["backbone"],

    function(Backbone) {

        var CaseStudy = Backbone.Model.extend({
          
            urlRoot: '/api/casestudies/',
            idAttribute: "id",
            
            defaults: {
                id: '',
                name: ''
            },

        });
        return CaseStudy;
    }
);