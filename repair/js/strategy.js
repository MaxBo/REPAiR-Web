require(['models/casestudy', 'views/strategy/solutions',
    'views/strategy/strategy', 'app-config', 'utils/overrides', 'base'
], function (CaseStudy, SolutionsView, StrategyView, appConfig) {
    /**
     * entry point for views on subpages of "Changes" menu item
     *
     * @author Christoph Franke
     * @module Changes
     */

    renderWorkshop = function(caseStudy){
        var solutionsView = new SolutionsView({
            caseStudy: caseStudy,
            el: document.getElementById('solutions'),
            template: 'solutions-template'
        });
        var strategyView = new StrategyView({
            caseStudy: caseStudy,
            el: document.getElementById('strategy'),
            template: 'strategy-template'
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
