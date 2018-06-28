require(['d3', 'models/casestudy', 'views/status-quo/flows', 'views/status-quo/targets',
    'views/status-quo/challenges-aims', 'views/status-quo/sustainability',
    'views/status-quo/setup-flow-assessment', 
    'views/status-quo/workshop-flow-assessment', 'visualizations/mapviewer', 
    'app-config', 'utils/overrides', 'base'
], function (d3, CaseStudy, FlowsView, TargetsView, ChallengesAimsView,
    SustainabilityView, FlowAssessmentSetupView, FlowAssessmentWorkshopView,
    MapViewer, appConfig) {


renderFlowsView = function(caseStudy){
    var flowsView,
        el = document.getElementById('flows-content'),
        keyflowSelect = el.parentElement.querySelector('select[name="keyflow"]');
    keyflowSelect.disabled = false;
    keyflowSelect.selectedIndex = 0; // Mozilla does not reset selects on reload
    keyflowSelect.addEventListener('change', function(){
        if (flowsView) flowsView.close();
        flowsView = new FlowsView({ 
            caseStudy: caseStudy,
            el: el,
            template: 'flows-template',
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

renderFlowAssessmentWorkshopView = function(caseStudy){
    var assessmentView,
        el = document.getElementById('flow-assessment-content'),
        keyflowSelect = el.parentElement.querySelector('select[name="keyflow"]');
    keyflowSelect.disabled = false;
    keyflowSelect.selectedIndex = 0; // Mozilla does not reset selects on reload
    keyflowSelect.addEventListener('change', function(){
        if (assessmentView) assessmentView.close();
        assessmentView = new FlowAssessmentWorkshopView({ 
            caseStudy: caseStudy,
            el: el,
            template: 'setup-flow-assessment-template',
            keyflowId: keyflowSelect.value
        })
    })
};

renderWorkshop = function(caseStudy){
    renderFlowsView(caseStudy);
    var challengesView = new ChallengesAimsView({ 
        caseStudy: caseStudy,
        el: document.getElementById('challenges'),
        template: 'challenges-aims-template'
    })
    var targetsView = new TargetsView({ 
        caseStudy: caseStudy,
        el: document.getElementById('targets'),
        template: 'targets-template'
    })
    var evaluationView = new SustainabilityView({ 
        caseStudy: caseStudy,
        el: document.getElementById('sustainability-assessment'),
        template: 'sustainability-template'
    })
    renderFlowAssessmentView(caseStudy, FlowAssessmentWorkshopView,
                             'workshop-flow-assessment-template');
};

renderSetup = function(caseStudy){
    renderFlowsView(caseStudy);
    var challengesView = new ChallengesAimsView({ 
        caseStudy: caseStudy,
        el: document.getElementById('challenges'),
        template: 'challenges-aims-template', 
        mode: 1
    })
    var evaluationView = new SustainabilityView({ 
        caseStudy: caseStudy,
        el: document.getElementById('sustainability-assessment'),
        template: 'sustainability-template'
    })
    renderFlowAssessmentView(caseStudy, FlowAssessmentSetupView,
                             'setup-flow-assessment-template');
};

var session = appConfig.getSession(
    function(session){
        var mode = session['mode'],
            caseStudyId = session['casestudy'],
            caseStudy = new CaseStudy({id: caseStudyId});

        caseStudy.fetch({success: function(){
            if (Number(mode) == 1) {
                renderSetup(caseStudy);
            }
            else {
                renderWorkshop(caseStudy);
            }
        }});
});
});