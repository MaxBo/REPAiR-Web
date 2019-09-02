require(['models/casestudy', 'views/conclusions/setup-users',
         'views/conclusions/manage-notepad', 'views/conclusions/objectives',
         'views/conclusions/flow-targets', 'views/conclusions/strategies',
         'views/conclusions/modified-flows', 'views/status-quo/sustainability',
         'views/conclusions/conclusions',
         'models/indicator', 'collections/gdsecollection', 'app-config', 'utils/utils',
         'underscore', 'base'
], function (CaseStudy, SetupUsersView, SetupNotepadView, EvalObjectivesView,
             EvalFlowTargetsView, EvalStrategiesView, EvalModifiedFlowsView,
             SustainabilityView, ConclusionsView, Indicator, GDSECollection,
             appConfig, utils, _) {
    /**
     * entry point for views on subpages of "Conclusions" menu item
     *
     * @author Christoph Franke
     * @module Conclusions
     */

    var consensusLevels, sections, objectivesView, flowTargetsView,
        strategiesView, modifiedFlowsView, sustainabilityView, keyflowSelect,
        keyflows;

    renderSetup = function(caseStudy){
        var usersView = new SetupUsersView({
            caseStudy: caseStudy,
            el: document.getElementById('users')
        })
        var setupNotepadView = new SetupNotepadView({
            caseStudy: caseStudy,
            el: document.getElementById('notepad'),
            consensusLevels: consensusLevels,
            sections: sections
        })
        var sustainabilityView,
            el = document.getElementById('sustainability-content');
        keyflowSelect = el.parentElement.querySelector('select[name="keyflow"]');
        keyflowSelect.disabled = false;
        keyflowSelect.selectedIndex = 0; // Mozilla does not reset selects on reload
        keyflowSelect.addEventListener('change', function(){
            if (sustainabilityView) sustainabilityView.close();
            sustainabilityView = new SustainabilityView({
                caseStudy: caseStudy,
                el: el,
                template: 'sustainability-template',
                keyflow: keyflows.get(keyflowSelect.value)
            })
        })
    };

    renderWorkshop = function(caseStudy, keyflow, objectives,
                              participants, indicators, strategies, aims,
                              conclusions){
        if (participants.size() === 0){
            var warning = document.createElement('h3');
            warning.innerHTML = gettext('There are no specified users! Please go to setup mode.')
            document.getElementById('content').innerHTML = warning.outerHTML;
            return;
        }
        if (objectivesView) objectivesView.close();
        objectivesView = new EvalObjectivesView({
            caseStudy: caseStudy,
            el: document.getElementById('objectives'),
            template: 'objectives-template',
            keyflow: keyflow,
            users: participants,
            aims: aims,
            objectives: objectives
        })
        if (flowTargetsView) flowTargetsView.close();
        flowTargetsView = new EvalFlowTargetsView({
            caseStudy: caseStudy,
            el: document.getElementById('flow-targets'),
            template: 'flow-targets-template',
            keyflow: keyflow,
            users: participants,
            aims: aims,
            objectives: objectives,
            indicators: indicators
        })
        if (strategiesView) strategiesView.close();
        strategiesView = new EvalStrategiesView({
            caseStudy: caseStudy,
            keyflow: keyflow,
            el: document.getElementById('strategies'),
            template: 'strategies-template',
            users: participants,
            strategies: strategies
        })
        if (modifiedFlowsView) modifiedFlowsView.close();
        modifiedFlowsView = new EvalModifiedFlowsView({
            caseStudy: caseStudy,
            keyflow: keyflow,
            el: document.getElementById('modified-flows'),
            template: 'modified-flows-template',
            users: participants,
            indicators: indicators,
            strategies: strategies,
            objectives: objectives
        })
        if (sustainabilityView) sustainabilityView.close();
        sustainabilityView = new SustainabilityView({
            caseStudy: caseStudy,
            el: document.getElementById('sustainability'),
            template: 'sustainability-template',
            keyflow: keyflow
        })
    };

    function render(caseStudy, mode){
        // setup view has no keyflow selection
        if (Number(mode) == 1){
            renderSetup(caseStudy);
            return;
        }

        // the workshop view does have one
        keyflowSelect = document.getElementById('keyflow-select');
        var session = appConfig.session;
        document.getElementById('keyflow-warning').style.display = 'block';

        function renderKeyflow(keyflow){
            keyflowSelect.disabled = true;
            document.getElementById('keyflow-warning').style.display = 'none';
            var loader = new utils.Loader(document.getElementById('content'),
                                         { disable: true });
            loader.activate();
            var aims = new GDSECollection([], {
                apiTag: 'aims',
                apiIds: [caseStudy.id]
            });
            var users = new GDSECollection([], {
                apiTag: 'usersInCasestudy',
                apiIds: [caseStudy.id]
            });
            var indicators = new GDSECollection([], {
                apiTag: 'flowIndicators',
                apiIds: [caseStudy.id, keyflow.id],
                comparator: 'name',
                model: Indicator
            });
            var promises = [];
            promises.push(aims.fetch({
                data: { keyflow: keyflow.id },
                error: alert
            }));
            promises.push(users.fetch());
            promises.push(indicators.fetch());

            Promise.all(promises).then(function(){
                loader.deactivate();
                indicators.sort();
                var participants = users.filterBy({'gets_evaluated' : true});
                var strategies = new GDSECollection([], {
                    apiTag: 'strategies',
                    apiIds: [caseStudy.id, keyflow.id]
                });
                var objectives = new GDSECollection([], {
                    apiTag: 'userObjectives',
                    apiIds: [caseStudy.id],
                    comparator: 'name'
                });
                promises.push(strategies.fetch({
                    data: { 'user__in': participants.pluck('id').join(',') },
                    error: alert
                }));
                // here we need profile resp. user id (same ids)
                // shitty naming, there is a chain of 3 different 'user' models
                promises.push(objectives.fetch({
                    data: { keyflow: keyflow.id, 'user__in': participants.pluck('user').join(',') },
                    error: alert
                }));
                Promise.all(promises).then(function(){
                    var promises = [];
                    objectives.sort();
                    objectives.forEach(function(objective){
                        var targetsInObj = new GDSECollection([], {
                                apiTag: 'flowTargets',
                                apiIds: [caseStudy.id, objective.id]
                            }),
                            aimId = objective.get('aim');
                        promises.push(targetsInObj.fetch({
                            success: function(){
                                objective.targets = targetsInObj;
                            },
                            error: alert
                        }));
                    });
                    Promise.all(promises).then(function(){
                        renderWorkshop(caseStudy, keyflow, objectives,
                                       participants, indicators, strategies, aims);
                        keyflowSelect.disabled = false;
                    });
                })
            })//.catch(function(res){
                //if (res.responseText)
                    //alert(res.responseText);
                //else alert(gettext('Error'))
                //loader.deactivate()
            //});
        }

        var keyflowSession = session.get('keyflow');
        if (keyflowSession != null){
            keyflowSelect.value = keyflowSession;
            // stored keyflow is not in select (most likely casestudy was accessed)
            if (keyflowSelect.selectedIndex === -1){
                keyflowSelect.selectedIndex = 0;
            }
            else {
                var keyflow = keyflows.get(parseInt(keyflowSession));
                renderKeyflow(keyflow);
            }
        }

        keyflowSelect.addEventListener('change', function(){
            var keyflowId = this.value,
                keyflow = keyflows.get(keyflowId);
            session.set('keyflow', keyflowId);
            session.save();

            renderKeyflow(keyflow);
        });

        var conclusionsView = new ConclusionsView({
            caseStudy: caseStudy,
            el: document.getElementById('conclusions'),
            template: 'conclusions-template',
            consensusLevels: consensusLevels,
            sections: sections,
            keyflows: keyflows
        })

        document.getElementById('add-conclusion').addEventListener('click', function(){
            var keyflowId = keyflowSelect.value;
            conclusionsView.addConclusion(keyflowId);
        });
    }

    appConfig.session.fetch({
        success: function(session){
            var mode = session.get('mode'),
                caseStudyId = session.get('casestudy'),
                caseStudy = new CaseStudy({id: caseStudyId});

            consensusLevels = new GDSECollection([], {
                apiTag: 'consensusLevels',
                apiIds: [caseStudyId],
                comparator: 'priority'
            });
            sections = new GDSECollection([], {
                apiTag: 'sections',
                apiIds: [caseStudyId],
                comparator: 'priority'
            });

            promises = [];
            promises.push(caseStudy.fetch())
            promises.push(consensusLevels.fetch());
            promises.push(sections.fetch());

            Promise.all(promises).then(function(){
                keyflows = new GDSECollection([], {
                    apiTag: 'keyflowsInCaseStudy',
                    apiIds: [caseStudyId]
                });
                keyflows.fetch({
                    success: function(){ render(caseStudy, mode); }
                })
            })
        }
    });
});

