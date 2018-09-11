require(['d3', 'models/casestudy', 'views/targets/sustainability-targets',
         'app-config', 'utils/overrides', 'base'
], function (d3, CaseStudy, SustainabilityTargetsView, appConfig) {

    /**
     * entry point for views on subpages of "Targets" menu item
     *
     * @author Christoph Franke
     * @module Targets
     */

    renderWorkshop = function(caseStudy){
        var flowTargetsView = new SustainabilityTargetsView({
            caseStudy: caseStudy,
            el: document.getElementById('sustainability-targets'),
            template: 'sustainability-targets-template'
        })
    };

    renderSetup = function(caseStudy){
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

