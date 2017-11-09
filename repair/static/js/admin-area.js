require(['./libs/domReady!', './require-config'], function (doc, config) {
  require(['jquery', 'app/models/casestudy', 'app/views/admin-data-entry',
           'app/views/admin-data-view', 'app/collections/flows', 
           'app/collections/activitygroups'], 
  function ($, CaseStudy, DataEntryView, DataView, Flows, ActivityGroups) {
  
    var caseStudySelect = document.getElementById('case-studies-select');
    var materialSelect = document.getElementById('flows-select');
    
    var dataView;
    var dataEntry;
  
    var renderDataView = function(){
      var caseStudyId = caseStudySelect.options[caseStudySelect.selectedIndex].value;
      var materialId = materialSelect.options[materialSelect.selectedIndex].value;
      var groupToGroup = new Flows({caseStudyId: caseStudyId, 
                                    materialId: materialId});
      if (dataView != null)
        dataView.close();
      
      var activityGroups = new ActivityGroups({caseStudyId: caseStudyId});
      dataView = new DataView({
        el: document.getElementById('data-view'),
        template: 'data-view-template',
        collection: groupToGroup,
        activityGroups: activityGroups
      });
    };
    
    // render data entry for currently selected casestudy
    var renderDataEntry = function(){
      var caseStudyId = caseStudySelect.options[caseStudySelect.selectedIndex].value;
      if (dataEntry != null)
        dataEntry.close();
        
      // create casestudy-object and render view on it (data will be fetched in view)
      var caseStudy = new CaseStudy({id: caseStudyId});
      dataEntry = new DataEntryView({
        el: document.getElementById('data-entry'),
        template: 'data-entry-template',
        model: caseStudy
      });
    };
  
    var refreshButton = document.getElementById('refresh-view-btn');
    
    // selection of casestudy changed -> render new view
    caseStudySelect.addEventListener('change', renderDataEntry);
    caseStudySelect.addEventListener('change', renderDataView);
    materialSelect.addEventListener('change', renderDataView);
    refreshButton.addEventListener('click', renderDataView);
    
    // initially show first case study (selected index 0)
    renderDataEntry();
    renderDataView();
  });
});