require(['./libs/domReady!', './require-config'], function (doc, config) {
  require(['jquery', 'app/models/casestudy', 'app/views/admin-data-entry',
           'app/views/admin-data-view', 'app/collections/flows',
           'app/collections/activitygroups', 'app/collections/materials',
           'app/collections/stocks', 'app-config', 'app/loader'],
  function ($, CaseStudy, DataEntryView, DataView, Flows, ActivityGroups,
            Materials, Stocks, appConfig) {

    var caseStudyId,
        caseStudy,
        activityGroups,
        materials;

    var dataView;
    var dataEntryView;

    var renderDataView = function(materialId, caseStudyId){
      var groupToGroup = new Flows([], {caseStudyId: caseStudyId,
                                        materialId: materialId});
      if (dataView != null)
        dataView.close();

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
    var renderDataEntry = function(caseStudy){
      if (dataEntryView != null)
        dataEntryView.close();

      // create casestudy-object and render view on it (data will be fetched in view)

      dataEntryView = new DataEntryView({
        el: document.getElementById('data-entry'),
        template: 'data-entry-template',
        model: caseStudy,
        activityGroups: activityGroups
      });
    };

    var renderCaseStudy = function(caseStudy){
      var caseStudyId = caseStudy.id;
      var flowInner = _.template(document.getElementById('flows-edit-template').innerHTML);
      var el = document.getElementById('flows-edit');
      el.innerHTML = flowInner({casestudy: caseStudy.get('name'),
                                materials: materials});

      var materialSelect = document.getElementById('flows-select');
      var refreshButton = document.getElementById('refresh-view-btn');
      var onMaterialChange = function(){
        var materialId = materialSelect.options[materialSelect.selectedIndex].value;
        renderDataView(materialId, caseStudyId);
      }
      materialSelect.addEventListener('change', onMaterialChange);
      refreshButton.addEventListener('click', onMaterialChange);

      renderDataEntry(caseStudy);

      if (materials.length > 0){
        renderDataView(materials.first().id, caseStudyId);
      }
    }

    var session = appConfig.getSession(
      function(session){
        var caseStudyId = session['casestudy'];
        caseStudy = new CaseStudy({id: caseStudyId});
        activityGroups = new ActivityGroups({caseStudyId: caseStudyId});
        materials = new Materials({caseStudyId: caseStudyId});
        if (caseStudyId == null)
          return;
        var loader = new Loader(document.getElementById('flows-edit'),
                                {disable: true});
        $.when(caseStudy.fetch(), activityGroups.fetch(), materials.fetch()).then(function() {
          loader.remove();
          renderCaseStudy(caseStudy);
        });
    });
  });
});