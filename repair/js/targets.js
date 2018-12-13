require(['d3', 'models/casestudy', 'collections/gdsecollection',
         'views/targets/flow-targets', 'views/targets/ranking-objectives',
         'app-config', 'utils/utils', 'utils/overrides', 'base'
], function (d3, CaseStudy, GDSECollection, FlowTargetsView,
             RankingObjectivesView, appConfig, utils) {

    /**
     * entry point for views on subpages of "Targets" menu item
     *
     * @author Christoph Franke
     * @module Targets
     */

    var flowTargetsView, rankingObjectivesView;

    $('#sidebar a[data-toggle="pill"]').on('shown.bs.tab', function (e) {
        var target = $(e.target).attr("href") // activated tab
        if (target === '#flow-targets' && flowTargetsView){
            flowTargetsView.updateOrder();
        }
    });

    renderWorkshop = function(caseStudy, keyflowId, userObjectives, aims, keyflowName){
        if (flowTargetsView) flowTargetsView.close();
        flowTargetsView = new FlowTargetsView({
            caseStudy: caseStudy,
            keyflowId: keyflowId,
            keyflowName: keyflowName,
            aims: aims,
            userObjectives: userObjectives,
            el: document.getElementById('flow-targets'),
            template: 'flow-targets-template'
        })
        if (rankingObjectivesView) rankingObjectivesView.close();
        rankingObjectivesView = new RankingObjectivesView({
            caseStudy: caseStudy,
            keyflowId: keyflowId,
            keyflowName: keyflowName,
            aims: aims,
            userObjectives: userObjectives,
            el: document.getElementById('ranking-objectives'),
            template: 'ranking-objectives-template'
        })
    };

    renderSetup = function(caseStudy, keyflowId){
    };

    function render(caseStudy, mode){
        var keyflowSelect = document.getElementById('keyflow-select'),
            session = appConfig.session;
        document.getElementById('keyflow-warning').style.display = 'block';
        keyflowSelect.disabled = false;

        function renderKeyflow(keyflowId, keyflowName){
            document.getElementById('keyflow-warning').style.display = 'none';
            // all sub views of Targets work on the same aims and objectives
            var loader = new utils.Loader(document.getElementById('content'),
                                         { disable: true });
            loader.activate();
            var aims = new GDSECollection([], {
                apiTag: 'aims',
                apiIds: [caseStudy.id],
                comparator: 'priority'
            });
            var userObjectives = new GDSECollection([], {
                apiTag: 'userObjectives',
                apiIds: [caseStudy.id],
                comparator: 'priority'
            });
            userObjectives.sort();

            var promises = [];
            promises.push(aims.fetch({
                data: { keyflow: keyflowId },
                error: alert
            }));
            promises.push(userObjectives.fetch({
                data: { keyflow: keyflowId },
                error: alert
            }));

            Promise.all(promises).then(function(){
                loader.deactivate();
                if (Number(mode) == 1)
                    renderSetup(caseStudy, keyflowId);
                else
                    renderWorkshop(caseStudy, keyflowId, userObjectives, aims, keyflowName);
            });
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

            // atm there is nothing to do in setup mode
            if (Number(mode) == 1) return;

            caseStudy.fetch({success: function(){
                render(caseStudy, mode);
            }});
        }
    });
});

