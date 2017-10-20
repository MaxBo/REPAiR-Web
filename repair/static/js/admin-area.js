require(['./libs/domReady!', './require-config'], function (doc, config) {
  require(['jquery', 'app/models/CaseStudy', 'app/views/admin-edit-flows-view'], 
  function ($, CaseStudy, EditFlowsView) {
  
    var caseStudy = new CaseStudy({id: 1});
    var view = new EditFlowsView({el: document.getElementById('edit-flows')});
    
  });
});