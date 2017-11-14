require(['./libs/domReady!', './require-config'], function (doc, config) {
  require(['jquery', 'app/models/casestudy', 'app/views/admin-data-entry',
           'app/views/admin-data-view', 'app/collections/flows', 
           'app/collections/activitygroups', 'app/collections/materials',
           'app/collections/stocks','app-config', 'app/loader'], 
  function ($, CaseStudy, DataEntryView, DataView, Flows, ActivityGroups,
            Materials, Stocks, appConfig) {
    
  
    
    var caseStudyId;
    var materialSelect = document.getElementById('flows-select');
    
    var dataView;
    var dataEntryView;
    var materials;
  
    var renderDataView = function(event){
      var materialId = materialSelect.options[materialSelect.selectedIndex].value;
      var groupToGroup = new Flows([], {caseStudyId: caseStudyId, 
                                        materialId: materialId});
      if (dataView != null)
        dataView.close();
      
      var activityGroups = new ActivityGroups({caseStudyId: caseStudyId});
      var stocks = new Stocks([], {caseStudyId: caseStudyId, materialId: materialId});
      dataView = new DataView({
        el: document.getElementById('data-view'),
        template: 'data-view-template',
        collection: groupToGroup,
        activityGroups: activityGroups,
        stocks: stocks
      });
    };
    
    // render data entry for currently selected casestudy
    var renderDataEntry = function(caseStudyId){
      if (dataEntryView != null)
        dataEntryView.close();
        
      // create casestudy-object and render view on it (data will be fetched in view)
      var caseStudy = new CaseStudy({id: caseStudyId});
      dataEntryView = new DataEntryView({
        el: document.getElementById('data-entry'),
        template: 'data-entry-template',
        model: caseStudy
      });
    };
    
    var renderCaseStudy = function(){
      materials = new Materials({caseStudyId: caseStudyId});
      var loader = new Loader(document.getElementById('flows-edit'), 
                              {disable: true});
      materials.fetch({success: function(){
        for(var i = materialSelect.options.length - 1 ; i >= 0 ; i--){
          materialSelect.remove(i);
        }
        materials.each(function(material){
          var option = document.createElement("option");
          option.text = material.get('material').code;
          option.value = material.id;
          materialSelect.add(option);
        });
        loader.remove();
        renderDataEntry(caseStudyId);
        renderDataView();
      }});
    }
  
    var refreshButton = document.getElementById('refresh-view-btn');
    
    // selection of casestudy changed -> render new view
    materialSelect.addEventListener('change', renderDataView);
    refreshButton.addEventListener('click', renderDataView);
    
    // initially show first case study (selected index 0)
    
    
    var session = appConfig.getSession(
      function(session){
        console.log(session)
        caseStudyId = session['casestudy'];
        renderCaseStudy();
    });
  });
});