define(['d3', 'models/casestudy',
    'views/study-area/workshop-maps', 'views/study-area/setup-maps',
    'views/study-area/charts', 'views/study-area/stakeholders',
    'views/study-area/keyflows',
    'app-config', 'base',
    'static/css/study-area.css'
], function(d3, CaseStudy, BaseMapView, SetupMapView, BaseChartsView,
    StakeholdersView, KeyflowsView, appConfig) {

    /**
     * entry point for views on subpages of "Study Area" menu item
     *
     * @author Christoph Franke
     * @module StudyArea
     */

    function renderWorkshop(caseStudy){
        var mapsView = new BaseMapView({
            template: 'base-maps-template',
            el: document.getElementById('base-map-content'),
            caseStudy: caseStudy
        });
        var chartsView = new BaseChartsView({
            template: 'base-charts-template',
            el: document.getElementById('base-charts-content'),
            caseStudy: caseStudy
        });
        var stakeholdersView = new StakeholdersView({
            template: 'stakeholders-template',
            el: document.getElementById('stakeholders-content'),
            caseStudy: caseStudy
        });
        var keyflowsView = new KeyflowsView({
            template: 'keyflows-template',
            el: document.getElementById('keyflows-content'),
            caseStudy: caseStudy
        });
    }

    function renderSetup(caseStudy){
        var mapsView = new SetupMapView({
            template: 'setup-maps-template',
            el: document.getElementById('base-map-content'),
            caseStudy: caseStudy
        });
        var chartsView = new BaseChartsView({
            template: 'base-charts-template',
            el: document.getElementById('base-charts-content'),
            caseStudy: caseStudy,
            mode: 1
        });
        var stakeholdersView = new StakeholdersView({
            template: 'stakeholders-template',
            el: document.getElementById('stakeholders-content'),
            caseStudy: caseStudy,
            mode: 1
        });
        var keyflowsView = new KeyflowsView({
            template: 'keyflows-template',
            el: document.getElementById('keyflows-content'),
            caseStudy: caseStudy,
            mode: 1
        });
    }

    appConfig.session.fetch({
        success: function(session){
            var mode = session.get('mode'),
                caseStudyId = session.get('casestudy'),
                caseStudy = new CaseStudy({id: caseStudyId});

            caseStudy.fetch({success: function(){
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
