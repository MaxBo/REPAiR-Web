require(['models/casestudy', 'models/gdsemodel', 'views/strategy/solutions',
    'views/strategy/strategy', 'app-config', 'utils/utils',
    'utils/overrides', 'base'
], function (CaseStudy, GDSEModel, SolutionsView, StrategyView, appConfig, utils) {
    /**
     * entry point for views on subpages of "Changes" menu item
     *
     * @author Christoph Franke
     * @module Changes
     */

    var solutionsView, strategyView;

    renderWorkshop = function(caseStudy, keyflow, keyflowName){
        if (solutionsView) solutionsView.close();
        solutionsView = new SolutionsView({
            caseStudy: caseStudy,
            el: document.getElementById('solutions'),
            template: 'solutions-template',
            keyflowId: keyflow.id,
            keyflowName: keyflowName
        });
        if (strategyView) strategyView.close();
        var strategyView = new StrategyView({
            caseStudy: caseStudy,
            el: document.getElementById('strategy'),
            template: 'strategy-template',
            keyflowId: keyflow.id,
            keyflowName: keyflowName
        })
    }

    renderSetup = function(caseStudy, keyflow, keyflowName){
        if(solutionsView) solutionsView.close();
        solutionsView = new SolutionsView({
            caseStudy: caseStudy,
            el: document.getElementById('solutions'),
            template: 'solutions-template',
            mode: 1,
            keyflowId: keyflow.id,
            keyflowName: keyflowName
        })
        loader = new utils.Loader(document.getElementById('graph'), {disable: true})
        // lazy way to reset the button to build graph
        var btn = document.getElementById('build-graph'),
            note = document.getElementById('graph-note'),
            clone = btn.cloneNode(true);
        note.innerHTML = keyflow.get('graph_build');
        btn.parentNode.replaceChild(clone, btn);
        clone.addEventListener('click', function(){
            loader.activate();
            var url = '/api/casestudies/{0}/keyflows/{1}/build_graph/'.format(caseStudy.id, keyflow.id);
            fetch(url).then(
                function(response) {
                    if (!response.ok) {
                        throw Error(response.statusText);
                    }
                    loader.deactivate();
                    return response.json();
                }).then(function(json) {
                    note.innerHTML = json['graph_build'];
                    alert(gettext('Graph was successfully build.'));
                }).catch(function(error) {
                    alert(error);
            });
            
        })
    };

    function render(caseStudy, mode){
        var keyflowSelect = document.getElementById('keyflow-select'),
            session = appConfig.session;
        document.getElementById('keyflow-warning').style.display = 'block';
        keyflowSelect.disabled = false;

        function renderKeyflow(keyflowId, keyflowName){
            var keyflow = new GDSEModel(
                {id: keyflowId}, 
                {
                    apiTag: 'keyflowsInCaseStudy',
                    apiIds: [caseStudy.id]
                }
            )
            keyflow.fetch({
                success: function(){
                    document.getElementById('keyflow-warning').style.display = 'none';
                    if (Number(mode) == 1)
                        renderSetup(caseStudy, keyflow, keyflowName);
                    else
                        renderWorkshop(caseStudy, keyflow, keyflowName);
                },
                error: alert
            })
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
