require(['./libs/domReady!', './require-config'], function (doc, config) {
  require(['jquery', 'app/models/casestudy', 'app/views/admin-data-entry',
           'app/views/admin-data-view', 'app/views/admin-edit-actors', 
           'app/collections/flows', 'app/collections/activities', 'app/collections/actors',
           'app/collections/activitygroups', 'app/collections/materials',
           'app/collections/stocks', 'app-config', 'app/loader'],
  function ($, CaseStudy, DataEntryView, DataView, EditActorsView, Flows, 
            Activities, Actors, ActivityGroups, Materials, Stocks, appConfig) {

    var caseStudyId,
        caseStudy,
        activityGroups,
        materials,
        activities;

    var dataView,
        dataEntryView,
        editActorsView;

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
        activityGroups: activityGroups,
        activities: activities
      });
    };
    
    var renderEditActors = function(caseStudy){
      if (editActorsView != null)
        editActorsView.close();

      // create casestudy-object and render view on it (data will be fetched in view)

      editActorsView = new EditActorsView({
        el: document.getElementById('actors-edit'),
        template: 'actors-edit-template',
        model: caseStudy,
        collection: new Actors({caseStudyId: caseStudy.id}),
        activities: activities,
        onUpload: function(){renderEditActors(caseStudy)}
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
      var onMaterialChange = function(rerenderEntry){
        var materialId = materialSelect.options[materialSelect.selectedIndex].value;
        renderDataView(materialId, caseStudyId);
        // can't safely add this inside view, because selector is not part of it's template
        if (rerenderEntry == true)
          dataEntryView.renderDataEntry();
      }
      materialSelect.addEventListener('change', function(){onMaterialChange(true)});
      refreshButton.addEventListener('click', onMaterialChange);

      renderDataEntry(caseStudy);
      renderEditActors(caseStudy);

      if (materials.length > 0){
        renderDataView(materials.first().id, caseStudyId);
      }
    }

    var session = appConfig.getSession(
      function(session){
        var caseStudyId = session['casestudy'];
        caseStudy = new CaseStudy({id: caseStudyId});
        activityGroups = new ActivityGroups({caseStudyId: caseStudyId});
        activities = new Activities({caseStudyId: caseStudyId});
        materials = new Materials({caseStudyId: caseStudyId});
        if (caseStudyId == null)
          return;
        var loader = new Loader(document.getElementById('content'),
                                {disable: true});
        $.when(caseStudy.fetch(), activityGroups.fetch(), 
               materials.fetch(), activities.fetch()).then(function() {
          loader.remove();
          renderCaseStudy(caseStudy);
        });
    });
  });
});