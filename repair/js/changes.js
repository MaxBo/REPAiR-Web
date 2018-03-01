require(['models/casestudy', 'views/changes/solutions', 
         'app-config', 'utils/overrides', 'base'
], function (CaseStudy, SolutionsView, appConfig) {
  
  var session = appConfig.getSession(
    function(session){
      var mode = session['mode'];
      if (Number(mode) == 1) {
        var caseStudyId = session['casestudy'];
        caseStudy = new CaseStudy({id: caseStudyId});
      
        caseStudy.fetch({success: function(){
          renderSetup(caseStudy)
        }});
      }
      else
        renderWorkshop()
  });

  renderWorkshop = function(){
  }
  
  renderSetup = function(caseStudy){
    var solutionsView = new SolutionsView({ 
      caseStudy: caseStudy,
      el: document.getElementById('solutions-setup'),
      template: 'solutions-template'
    })
  };
});