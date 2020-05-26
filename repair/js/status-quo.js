require(['d3', 'models/casestudy', 'views/status-quo/workshop-flows',
    'views/status-quo/setup-flows',
    'views/status-quo/objectives', 'views/status-quo/setup-flow-assessment',
    'views/study-area/workshop-maps', 'views/study-area/setup-maps',
    'views/status-quo/workshop-flow-assessment', 'views/conclusions/reports',
    'collections/gdsecollection', 'app-config', 'utils/overrides', 'base',
    'static/css/status-quo.css'
], function (d3, CaseStudy, FlowsWorkshopView, FlowsSetupView,
    ChallengesAimsView, FlowAssessmentSetupView, BaseMapView,
    SetupMapView, FlowAssessmentWorkshopView, ReportsView, GDSECollection,
    appConfig) {

    /**
     * entry point for views on subpages of "StatusQuo" menu item
     *
     * @author Christoph Franke
     * @module StatusQuo
     */

    renderReports = function(caseStudy, reports, mode){
        var reports_li = document.querySelector('a[href="#reports"]').parentNode,
            setupMode = Number(mode) == 1;
        if (setupMode || reports.length > 0){
            var reportsView = new ReportsView({
                caseStudy: caseStudy,
                el: document.getElementById('reports'),
                template: 'reports-template',
                setupMode: setupMode,
                reports: reports
            });
            reports_li.style.display = 'block';
        }
        if (!setupMode && reports.length == 0) {
            reports_li.style.display = 'none';
        }
    }

    renderFlowsView = function(caseStudy, View, template){
        var flowsView,
            el = document.getElementById('flows-content'),
            keyflowSelect = el.parentElement.querySelector('select[name="keyflow"]');
        keyflowSelect.disabled = false;
        keyflowSelect.selectedIndex = 0; // Mozilla does not reset selects on reload
        keyflowSelect.addEventListener('change', function(){
            if (flowsView) flowsView.close();
            flowsView = new View({
                caseStudy: caseStudy,
                el: el,
                template: template,
                keyflowId: keyflowSelect.value
            })
        })
    };

    renderFlowAssessmentView = function(caseStudy, View, template){
        var assessmentView,
            el = document.getElementById('flow-assessment-content'),
            keyflowSelect = el.parentElement.querySelector('select[name="keyflow"]');
        keyflowSelect.disabled = false;
        keyflowSelect.selectedIndex = 0; // Mozilla does not reset selects on reload
        keyflowSelect.addEventListener('change', function(){
            if (assessmentView) assessmentView.close();
            assessmentView = new View({
                caseStudy: caseStudy,
                el: el,
                template: template,
                keyflowId: keyflowSelect.value
            })
        })
    };

    renderWorkshop = function(caseStudy){
        var challengesView = new ChallengesAimsView({
            caseStudy: caseStudy,
            el: document.getElementById('challenges'),
            template: 'challenges-aims-template'
        })
        var mapsView = new BaseMapView({
            template: 'base-maps-template',
            el: document.getElementById('base-map-content'),
            caseStudy: caseStudy,
            tag: 'wastescapes'
        });
        renderFlowAssessmentView(caseStudy, FlowAssessmentWorkshopView,
                                 'workshop-flow-assessment-template');
        renderFlowsView(caseStudy, FlowsWorkshopView, 'workshop-flows-template');

    };

    renderSetup = function(caseStudy){
        var challengesView = new ChallengesAimsView({
            caseStudy: caseStudy,
            el: document.getElementById('challenges'),
            template: 'challenges-aims-template',
            mode: 1
        })
        var mapsView = new SetupMapView({
            template: 'setup-maps-template',
            el: document.getElementById('base-map-content'),
            caseStudy: caseStudy,
            tag: 'wastescapes'
        });
        renderFlowAssessmentView(caseStudy, FlowAssessmentSetupView,
                                 'setup-flow-assessment-template');
        renderFlowsView(caseStudy, FlowsSetupView, 'setup-flows-template');
    };

    appConfig.session.fetch({
        success: function(session){
            var mode = session.get('mode'),
                caseStudyId = session.get('casestudy'),
                caseStudy = new CaseStudy({id: caseStudyId});

            caseStudy.fetch({success: function(){
                var reports = new GDSECollection([], {
                    apiTag: 'statusQuoReports',
                    apiIds: [ caseStudy.id ]
                });
                reports.fetch({
                    success: function(){renderReports(caseStudy, reports, mode)},
                    error: alert
                })
                if (Number(mode) == 1) {
                    renderSetup(caseStudy);
                }
                else {
                    renderWorkshop(caseStudy);
                }

            }});
        }
    });
});
