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

    var flowTargetsView, rankingObjectivesView,
        keyflowSelect = document.getElementById('keyflow-select');


    $('#sidebar a[data-toggle="pill"]').on('shown.bs.tab', function (e) {
        if (keyflowSelect.value == -1) return;
        var target = $(e.target).attr("href") // activated tab
        if (target === '#flow-targets' && flowTargetsView){
            flowTargetsView.updateOrder();
        }
    });

    renderWorkshop = function(caseStudy, keyflowId, userObjectives, aims, keyflowName){
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
        if (flowTargetsView) flowTargetsView.close();
        var targetsDiv = document.getElementById('flow-targets');
        if ( keyflowId != -1 ) {
            flowTargetsView = new FlowTargetsView({
                caseStudy: caseStudy,
                keyflowId: keyflowId,
                keyflowName: keyflowName,
                aims: aims,
                userObjectives: userObjectives,
                el: targetsDiv,
                template: 'flow-targets-template'
            })
        }
        else{
            var warning = document.createElement('h3');
            warning.innerHTML = gettext("Flow targets can't be set for general objectives.<br><br>" +
                                        "Please select a keyflow inside the side-menu.")
            targetsDiv.innerHTML = warning.outerHTML;
        }
    };

    renderSetup = function(caseStudy){
        var button = document.getElementById('upload-year-btn'),
            input = document.querySelector('input[name="year"]');
        input.value = caseStudy.get('properties')['target_year'];
        button.addEventListener('click', function(){
            caseStudy.save(
                { 'target_year': input.value },
                {
                    patch: true,
                    success: function(){ alert('success') },
                    error: function(){ alert('error') }
                }
            )
        })
    };

    function render(caseStudy, mode){
        if (Number(mode) == 1){
            renderSetup(caseStudy);
            return;
        }
        var session = appConfig.session;
        keyflowSelect.disabled = false;


        function renderKeyflow(keyflowId, keyflowName){
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

            var promises = [],
                // "general" selected -> query keyflow == null
                data = (keyflowId == -1) ? { 'keyflow__isnull': true}: { keyflow: keyflowId };
            promises.push(aims.fetch({
                data: data,
                error: alert
            }));
            promises.push(userObjectives.fetch({
                data: data,
                error: alert
            }));

            Promise.all(promises).then(function(){
                loader.deactivate();
                aims.sort();
                userObjectives.sort();
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
            var keyflowName = keyflowSelect.options[keyflowSelect.selectedIndex].text;
            renderKeyflow(keyflowSelect.value, keyflowName);
        }

        keyflowSelect.addEventListener('change', function(){
            var keyflowId = this.value,
                keyflowName = this.options[this.selectedIndex].text;
            if (this.value != -1){
                session.set('keyflow', keyflowId);
                session.save();
            }
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

