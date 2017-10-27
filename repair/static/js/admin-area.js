require(['./libs/domReady!', './require-config'], function (doc, config) {
  require(['jquery', 'app/models/casestudy', 'app/views/admin-edit-flows-view'], 
  function ($, CaseStudy, EditFlowsView) {
    
    // render view on currently selected casestudy
    var showSelectedCaseStudy = function(){
      var id = caseStudySelect.options[caseStudySelect.selectedIndex].value;
      if (this.view != null)
        this.view.close();
        
      // create casestudy-object and render view on it (data will be fetched in view)
      var caseStudy = new CaseStudy({id: id});
      this.view = new EditFlowsView({
        el: document.getElementById('edit-flows'),
        model: caseStudy
      });
    };
  
    var caseStudySelect = document.getElementById('case-studies-select');    
    caseStudySelect.addEventListener('change', showSelectedCaseStudy);
    
    // initially show first case study (selected index 0)
    showSelectedCaseStudy();
  });
});