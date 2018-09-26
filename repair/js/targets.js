require(['d3', 'models/casestudy', 'views/targets/sustainability-targets',
         'views/common/baseview', 'app-config', 'utils/overrides', 'base'
], function (d3, CaseStudy, SustainabilityTargetsView, FlowTargetsView,
            appConfig) {

    /**
     * entry point for views on subpages of "Targets" menu item
     *
     * @author Christoph Franke
     * @module Targets
     */

    var sustainabilityTargetsView, flowTargetsView;

    renderWorkshop = function(caseStudy, keyflowId){
        if (sustainabilityTargetsView) sustainabilityTargetsView.close();
        sustainabilityTargetsView = new SustainabilityTargetsView({
            caseStudy: caseStudy,
            keyflowId: keyflowId,
            el: document.getElementById('sustainability-targets'),
            template: 'sustainability-targets-template'
        })
        if (flowTargetsView) flowTargetsView.close();
        flowTargetsView = new FlowTargetsView({
            caseStudy: caseStudy,
            keyflowId: keyflowId,
            el: document.getElementById('flow-targets'),
            template: 'flow-targets-template'
        })
        flowTargetsView.render();
    };

    renderSetup = function(caseStudy, keyflowId){
    };

    function render(caseStudy, mode){
        var keyflowSelect = document.getElementById('keyflow-select'),
            session = appConfig.session;
        document.getElementById('keyflow-warning').style.display = 'block';
        keyflowSelect.disabled = false;

        function renderKeyflow(keyflowId){
            document.getElementById('keyflow-warning').style.display = 'none';
            if (Number(mode) == 1)
                renderSetup(caseStudy, keyflowId);
            else
                renderWorkshop(caseStudy, keyflowId);
        }

        var keyflowSession = session.get('keyflow');
        if (keyflowSession != null){
            keyflowSelect.value = keyflowSession;
            // stored keyflow is not in select (most likely casestudy was accessed)
            if (keyflowSelect.selectedIndex === -1){
                keyflowSelect.selectedIndex = 0;
            }
            else renderKeyflow(parseInt(keyflowSession));
        }

        keyflowSelect.addEventListener('change', function(){
            var keyflowId = this.value;
            session.set('keyflow', keyflowId);
            session.save();
            renderKeyflow(keyflowId);
        });
    }

    appConfig.session.fetch({
        success: function(session){
            var mode = session.get('mode'),
                caseStudyId = session.get('casestudy'),
                caseStudy = new CaseStudy({id: caseStudyId});

            // atm there is nothing to do in setup mode
            if (Number(mode) == 1) return;

            caseStudy.fetch({success: function(){
                render(caseStudy, mode);
            }});
        }
    });
});
