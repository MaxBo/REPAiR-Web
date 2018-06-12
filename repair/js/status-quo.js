require(['d3', 'models/casestudy', 'views/status-quo/flows', 'views/status-quo/targets',
    'views/status-quo/challenges-aims', 'views/status-quo/sustainability',
    'visualizations/mapviewer', 
    'app-config', 'utils/overrides', 'base'
], function (d3, CaseStudy, FlowsView, TargetsView, ChallengesAimsView, 
    SustainabilityView, MapViewer, appConfig) {


renderFlowsView = function(caseStudy){
    var keyflowSelect = document.querySelector('select[name="keyflow"]'),
        flowsView;
    keyflowSelect.disabled = false;
    keyflowSelect.addEventListener('change', function(){
        if (flowsView) flowsView.close();
        flowsView = new FlowsView({ 
            caseStudy: caseStudy,
            el: document.getElementById('flows-content'),
            template: 'flows-template',
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