require(['models/casestudy', 'collections/gdsecollection', 'views/strategy/workshop-solutions',
         'views/strategy/setup-solutions', 'views/strategy/setup-solutions-logic',
         'views/strategy/strategy', 'app-config', 'utils/utils', 'utils/overrides', 'base'
], function (CaseStudy, GDSECollection, SolutionsWorkshopView, SolutionsSetupView, SolutionsLogicView,
             StrategyView, appConfig, utils) {
    /**
     * entry point for views on subpages of "Changes" menu item
     *
     * @author Christoph Franke
     * @module Changes
     */

    var solutionsView, strategyView, solutionsLogicView;

    renderWorkshop = function(caseStudy, keyflowId, keyflowName){
        if (solutionsView) solutionsView.close();
        solutionsView = new SolutionsWorkshopView({
            caseStudy: caseStudy,
            el: document.getElementById('solutions'),
            template: 'solutions-workshop-template',
            keyflowId: keyflowId,
            keyflowName: keyflowName
        });
        if (strategyView) strategyView.close();
        var strategyView = new StrategyView({
            caseStudy: caseStudy,
            el: document.getElementById('strategy'),
            template: 'strategy-template',
            keyflowId: keyflowId,
            keyflowName: keyflowName
        })
    }

    renderSetup = function(caseStudy, keyflowId, keyflowName, solutions, categories){
        if(solutionsView) solutionsView.close();
        solutionsView = new SolutionsSetupView({
            caseStudy: caseStudy,
            el: document.getElementById('solutions'),
            template: 'solutions-setup-template',
            keyflowId: keyflowId,
            keyflowName: keyflowName,
            solutions: solutions,
            categories: categories
        })
        if(solutionsLogicView) solutionsLogicView.close();
        solutionsLogicView = new SolutionsLogicView({
            caseStudy: caseStudy,
            el: document.getElementById('solutions-logic'),
            template: 'solutions-logic-template',
            keyflowId: keyflowId,
            solutions: solutions,
            categories: categories
        })
    };

    function render(caseStudy, mode){
        var keyflowSelect = document.getElementById('keyflow-select'),
            session = appConfig.session;
        document.getElementById('keyflow-warning').style.display = 'block';
        keyflowSelect.disabled = false;

        function renderKeyflow(keyflowId, keyflowName){
            document.getElementById('keyflow-warning').style.display = 'none';
            if (Number(mode) == 1){
                var loader = new utils.Loader(document.getElementById('content'),
                                             { disable: true });
                var solutions = new GDSECollection([], {
                    apiTag: 'solutions',
                    apiIds: [caseStudy.id, keyflowId],
                    comparator: 'name'
                });
                var categories = new GDSECollection([], {
                    apiTag: 'solutionCategories',
                    apiIds: [caseStudy.id, keyflowId]
                });
                loader.activate();
                Promise.all([solutions.fetch(), categories.fetch()]).then(function(){
                    solutions.sort();
                    renderSetup(caseStudy, keyflowId, keyflowName, solutions, categories);
                    loader.deactivate();
                })
            }
            else
                renderWorkshop(caseStudy, keyflowId, keyflowName);
        }

        var keyflowSession = session.get('keyflow');
        if (keyflowSession != null){
            keyflowSelect.value = keyflowSession;
            // stored keyflow is not in select (most likely casestudy was accessed)
            if (keyflowSelect.selectedIndex === -1){
                keyflowSelect.selectedIndex = 0;
            }
            else {
                var keyflowName = keyflowSelect.options[keyflowSelect.selectedIndex].text;
                renderKeyflow(parseInt(keyflowSession), keyflowName);
            }
        }

        keyflowSelect.addEventListener('change', function(){
            var keyflowId = this.value,
                keyflowName = this.options[this.selectedIndex].text;
            session.set('keyflow', keyflowId);
            session.save();
            renderKeyflow(keyflowId, keyflowName);
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
