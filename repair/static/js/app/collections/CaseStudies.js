define(["backbone", "app/models/CaseStudy"],

    function(Backbone, CaseStudy) {

        var CaseStudies = Backbone.Collection.extend({
            url: '/api/casestudy/',
            model: CaseStudy
        });
        
        return CaseStudies;
    }
);