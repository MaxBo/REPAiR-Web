require(['models/casestudy', 'views/conclusions/setup-users',
         'views/conclusions/manage-notepad', 'views/conclusions/objectives',
         'views/conclusions/flow-targets', 'views/conclusions/strategies',
         'views/conclusions/modified-flows', 'views/conclusions/sustainability',
         'models/indicator', 'collections/gdsecollection', 'app-config', 'utils/utils',
         'underscore', 'html2canvas', 'viewerjs', 'base', 'viewerjs/dist/viewer.css'
], function (CaseStudy, SetupUsersView, SetupNotepadView, EvalObjectivesView,
             EvalFlowTargetsView, EvalStrategiesView, EvalModifiedFlowsView,
             SustainabilityView, Indicator, GDSECollection, appConfig,
             utils, _, html2canvas, Viewer) {
    /**
     * entry point for views on subpages of "Conclusions" menu item
     *
     * @author Christoph Franke
     * @module Conclusions
     */

    var consensusLevels, sections, modal, objectivesView, flowTargetsView,
        strategiesView, modifiedFlowsView, sustainabilityView;


    html2image = function(container, onSuccess){
        html2canvas(container).then(canvas => {
            var data = canvas.toDataURL("image/png");
            onSuccess(data);
        });
    }

    addConclusion = function(){
        var html = document.getElementById('conclusion-template').innerHTML,
            template = _.template(html);
        if (!modal) {
            modal = document.getElementById('conclusion-modal');
            $(modal).on('shown.bs.modal', function() {
                console.log('show')
                new Viewer.default(modal.querySelector('img'));
            });
        }
        html2image(document.getElementById('content'), function(image){
            modal.innerHTML = template({
                consensusLevels: consensusLevels,
                sections: sections,
                image: image
            });
            $(modal).modal('show');
        })
    }

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
            el = document.getElementById('sustainability-content'),
            keyflowSelect = el.parentElement.querySelector('select[name="keyflow"]');
        keyflowSelect.disabled = false;
        keyflowSelect.selectedIndex = 0; // Mozilla does not reset selects on reload
        keyflowSelect.addEventListener('change', function(){
            if (sustainabilityView) sustainabilityView.close();
            sustainabilityView = new SustainabilityView({
                caseStudy: caseStudy,
                el: el,
                template: 'sustainability-template',
                keyflowId: keyflowSelect.value
            })
        })
    };

    renderWorkshop = function(caseStudy, keyflowId, keyflowName, objectives,
                              participants, indicators, strategies, aims){
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
            keyflowId: keyflowId,
            keyflowName: keyflowName,
            users: participants,
            aims: aims,
            objectives: objectives
        })
        if (flowTargetsView) flowTargetsView.close();
        flowTargetsView = new EvalFlowTargetsView({
            caseStudy: caseStudy,
            el: document.getElementById('flow-targets'),
            template: 'flow-targets-template',
            keyflowId: keyflowId,
            keyflowName: keyflowName,
            users: participants,
            aims: aims,
            objectives: objectives,
            indicators: indicators
        })
        if (strategiesView) strategiesView.close();
        strategiesView = new EvalStrategiesView({
            caseStudy: caseStudy,
            keyflowId: keyflowId,
            keyflowName: keyflowName,
            el: document.getElementById('strategies'),
            template: 'strategies-template',
            users: participants,
            strategies: strategies
        })
        if (modifiedFlowsView) modifiedFlowsView.close();
        modifiedFlowsView = new EvalModifiedFlowsView({
            caseStudy: caseStudy,
            keyflowId: keyflowId,
            el: document.getElementById('modified-flows'),
            template: 'modified-flows-template',
            users: participants,
            keyflowName: keyflowName,
            indicators: indicators,
            strategies: strategies,
            objectives: objectives
        })
        if (sustainabilityView) sustainabilityView.close();
        sustainabilityView = new SustainabilityView({
            caseStudy: caseStudy,
            el: document.getElementById('sustainability'),
            template: 'sustainability-template',
            keyflowId: keyflowId
        })

        document.getElementById('add-conclusion').addEventListener('click', addConclusion);
    };

    function render(caseStudy, mode){
        // setup view has no keyflow selection
        if (Number(mode) == 1){
            renderSetup(caseStudy);
            return;
        }

        // the workshop view does have one
        var keyflowSelect = document.getElementById('keyflow-select'),
            session = appConfig.session;
        document.getElementById('keyflow-warning').style.display = 'block';
        keyflowSelect.disabled = false;

        function renderKeyflow(keyflowId, keyflowName){
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
                apiIds: [caseStudy.id, keyflowId],
                comparator: 'name',
                model: Indicator
            });
            var promises = [];
            promises.push(aims.fetch({
                data: { keyflow: keyflowId },
                error: alert
            }));
            promises.push(users.fetch());
            promises.push(indicators.fetch());

            Promise.all(promises).then(function(){
                loader.deactivate();
                var participants = users.filterBy({'gets_evaluated' : true});
                var strategies = new GDSECollection([], {
                    apiTag: 'strategies',
                    apiIds: [caseStudy.id, keyflowId]
                });
                var objectives = new GDSECollection([], {
                    apiTag: 'userObjectives',
                    apiIds: [caseStudy.id]
                });
                var promises = [];
                promises.push(strategies.fetch({
                    data: { 'user__in': participants.pluck('id').join(',') },
                    error: alert
                }));
                // here we need profile resp. user id (same ids)
                // shitty naming, there is a chain of 3 different 'user' models
                promises.push(objectives.fetch({
                    data: { keyflow: keyflowId, 'user__in': participants.pluck('user').join(',') },
                    error: alert
                }));
                Promise.all(promises).then(function(){
                    var promises = [];
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
                        renderWorkshop(caseStudy, keyflowId, keyflowName, objectives,
                                       participants, indicators, strategies, aims);
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
                render(caseStudy, mode);
            })
        }
    });
});

