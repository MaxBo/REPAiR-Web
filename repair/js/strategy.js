require(['models/casestudy', 'views/strategy/solutions',
    'views/strategy/strategy', 'app-config', 'utils/overrides', 'base'
], function (CaseStudy, SolutionsView, StrategyView, appConfig) {
    /**
     * entry point for views on subpages of "Changes" menu item
     *
     * @author Christoph Franke
     * @module Changes
     */

    renderWorkshop = function(caseStudy, keyflowId){
        var solutionsView = new SolutionsView({
            caseStudy: caseStudy,
            el: document.getElementById('solutions'),
            template: 'solutions-template',
            keyflowId: keyflowId
        });
        var strategyView = new StrategyView({
            caseStudy: caseStudy,
            el: document.getElementById('strategy'),
            template: 'strategy-template',
            keyflowId: keyflowId
        })
    }

    renderSetup = function(caseStudy, keyflowId){
        var solutionsView = new SolutionsView({
            caseStudy: caseStudy,
            el: document.getElementById('solutions'),
            template: 'solutions-template',
            mode: 1,
            keyflowId: keyflowId
        })
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
            renderKeyflow(parseInt(keyflowSession));
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

            caseStudy.fetch({success: function(){
                render(caseStudy, mode);
            }});
        }
    });
});
