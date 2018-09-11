require(['d3', 'models/casestudy', 'views/targets/sustainability-targets',
         'app-config', 'utils/overrides', 'base'
], function (d3, CaseStudy, SustainabilityTargetsView, appConfig) {

    /**
     * entry point for views on subpages of "Targets" menu item
     *
     * @author Christoph Franke
     * @module Targets
     */

    var sustainabilityTargetsView, flowTargetsView;

    renderWorkshop = function(caseStudy, keyflow){
        if (sustainabilityTargetsView) sustainabilityTargetsView.close();
        sustainabilityTargetsView = new SustainabilityTargetsView({
            caseStudy: caseStudy,
            el: document.getElementById('sustainability-targets'),
            template: 'sustainability-targets-template'
        })
    };

    renderSetup = function(caseStudy, keyflow){
    };


    function render(caseStudy, mode){

        var keyflowSelect = document.getElementById('keyflow-select');
        document.getElementById('keyflow-warning').style.display = 'block';
        keyflowSelect.addEventListener('change', function(){
            var keyflowId = this.value;
            document.getElementById('keyflow-warning').style.display = 'none';
            if (Number(mode) == 1) {
                renderSetup(caseStudy, keyflowId);
            }
            else {
                renderWorkshop(caseStudy, keyflowId);
            }
        });
        document.getElementById('keyflow-select').disabled = false;
    }

    appConfig.session.fetch({
        success: function(session){
            var mode = session.get('mode'),
                caseStudyId = session.get('casestudy'),
                caseStudy = new CaseStudy({id: caseStudyId});

            caseStudy.fetch({success: function(){
                render(caseStudy, mode);
            }});
        }
    });
});

