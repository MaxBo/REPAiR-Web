require(['models/casestudy', 'views/changes/solutions', 
         'app-config', 'utils/overrides', 'base'
], function (CaseStudy, SolutionsView, appConfig) {

  renderWorkshop = function(caseStudy){
    var solutionsView = new SolutionsView({ 
      caseStudy: caseStudy,
      el: document.getElementById('solutions'),
      template: 'solutions-template'
    })
  }
  
  renderSetup = function(caseStudy){
    var solutionsView = new SolutionsView({ 
      caseStudy: caseStudy,
      el: document.getElementById('solutions'),
      template: 'solutions-template',
      mode: 1
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