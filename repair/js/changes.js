require(['models/casestudy', 'views/changes/solutions',
    'views/changes/implementations', 'app-config', 'utils/overrides', 'base'
], function (CaseStudy, SolutionsView, ImplementationsView, appConfig) {

    renderWorkshop = function(caseStudy){
        var solutionsView = new SolutionsView({ 
            caseStudy: caseStudy,
            el: document.getElementById('solutions'),
            template: 'solutions-template'
        });
        var implementationsView = new ImplementationsView({ 
            caseStudy: caseStudy,
            el: document.getElementById('implementations'),
            template: 'implementations-template'
        })
    }

    renderSetup = function(caseStudy){
        var solutionsView = new SolutionsView({ 
            caseStudy: caseStudy,
            el: document.getElementById('solutions'),
            template: 'solutions-template',
            mode: 1
        })
    };

    appConfig.session.fetch({
        success: function(session){
            var mode = session.get('mode'),
                caseStudyId = session.get('casestudy'),
                caseStudy = new CaseStudy({id: caseStudyId});

            caseStudy.fetch({success: function(){
                if (Number(mode) == 1) {
                    renderSetup(caseStudy);
                }
                else {
                    renderWorkshop(caseStudy);
                }
            }});
        }
    });
});