define(["backbone", "app/models/CaseStudy"],

    function(Backbone, CaseStudy) {

        var CaseStudies = Backbone.Collection.extend({
            url: '/api/casestudies/',
            model: CaseStudy
        });
        
        return CaseStudies;
    }
);