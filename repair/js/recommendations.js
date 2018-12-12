require(['models/casestudy', 'views/recommendations/setup-users',
         'views/recommendations/objectives', 'views/recommendations/flow-targets',
         'collections/gdsecollection', 'app-config', 'utils/utils', 'base'
], function (CaseStudy, SetupUsersView, EvalObjectivesView, EvalFlowTargetsView,
             GDSECollection, appConfig, utils) {
    /**
     * entry point for views on subpages of "Recommendations" menu item
     *
     * @author Christoph Franke
     * @module Recommendations
     */

     var objectivesView;

    renderSetup = function(caseStudy){
        var usersView = new SetupUsersView({
            caseStudy: caseStudy
        })

    };

    renderWorkshop = function(caseStudy, keyflowId, keyflowName, users, aims, objectives){
        if (users.size() === 0){
            var warning = document.createElement('h3');
            warning.innerHTML = gettext('There are no specified users! Please go to setup mode.')
            document.getElementById('content').innerHTML = warning.outerHTML;
            return;
        }
        if (objectivesView) objectivesView.close();
        var objectivesView = new EvalObjectivesView({
            caseStudy: caseStudy,
            el: document.getElementById('objectives'),
            template: 'objectives-template',
            keyflowId: keyflowId,
            keyflowName: keyflowName,
            users: users,
            aims: aims,
            objectives: objectives
        })
        if (flowTargetsView) flowTargetsView.close();
        var flowTargetsView = new EvalFlowTargetsView({
            caseStudy: caseStudy,
            el: document.getElementById('flow-targets'),
            template: 'flow-targets-template',
            keyflowId: keyflowId,
            keyflowName: keyflowName,
            users: users,
            aims: aims,
            objectives: objectives
        })

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
            var objectives = new GDSECollection([], {
                apiTag: 'userObjectives',
                apiIds: [caseStudy.id]
            });
            var promises = [];
            promises.push(aims.fetch({
                data: { keyflow: keyflowId },
                error: alert
            }));
            promises.push(objectives.fetch({
                data: { keyflow: keyflowId, all: true },
                error: alert
            }));
            promises.push(users.fetch({error: alert}));

            Promise.all(promises).then(function(){
                loader.deactivate();
                var participants = users.filterBy({'gets_evaluated' : true});
                renderWorkshop(caseStudy, keyflowId, keyflowName, participants, aims, objectives);
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

            caseStudy.fetch({success: function(){
                render(caseStudy, mode);
            }});
        }
    });
});

