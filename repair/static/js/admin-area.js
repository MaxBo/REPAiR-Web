require(['./libs/domReady!', './require-config'], function (doc, config) {
  require(['app/models/casestudy', 'app/views/admin-data-entry',
           'app/views/admin-data-view', 'app/views/admin-edit-actors', 
           'app/collections/flows', 'app/collections/activities', 'app/collections/actors',
           'app/collections/activitygroups', 'app/collections/keyflows',
           'app/collections/stocks', 'app/collections/materials',
           'app/collections/products', 'app-config', 'app/loader'],
  function (CaseStudy, DataEntryView, DataView, EditActorsView, Flows, 
            Activities, Actors, ActivityGroups, Keyflows, Stocks, Materials,
            Products, appConfig) {

    var caseStudyId,
        caseStudy,
        activityGroups,
        keyflows,
        activities,
        materials;

    var dataView,
        dataEntryView,
        editActorsView;

    var renderDataView = function(keyflowId, caseStudyId){
      var groupToGroup = new Flows([], {caseStudyId: caseStudyId,
                                        keyflowId: keyflowId});
      if (dataView != null)
        dataView.close();

      var stocks = new Stocks([], {caseStudyId: caseStudyId, keyflowId: keyflowId});
      var products = new Products({caseStudyId: caseStudyId, keyflowId: keyflowId});
      dataView = new DataView({
        el: document.getElementById('data-view'),
        template: 'data-view-template',
        collection: groupToGroup,
        activityGroups: activityGroups,
        stocks: stocks,
        products: products
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
        activities: activities,
        materials: materials
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
                                keyflows: keyflows});

      var keyflowSelect = document.getElementById('flows-select');
      var onKeyflowChange = function(rerenderEntry){
        var keyflowId = keyflowSelect.options[keyflowSelect.selectedIndex].value;
        renderDataView(keyflowId, caseStudyId);
        // can't safely add this inside view, because selector is not part of it's template
        if (rerenderEntry == true)
          dataEntryView.renderDataEntry();
      }
      keyflowSelect.addEventListener('change', function(){onKeyflowChange(true)});
      
      // rerender view on data (aka sankey)
      document.getElementById('refresh-dataview-btn').addEventListener(
        'click', onKeyflowChange);
      // rerender view on data-entries
      document.getElementById('refresh-dataentry-btn').addEventListener(
        'click', function(){renderDataEntry(caseStudy)});

      renderDataEntry(caseStudy);
      renderEditActors(caseStudy);

      if (keyflows.length > 0){
        renderDataView(keyflows.first().id, caseStudyId);
      }
      
    }

    var session = appConfig.getSession(
      function(session){
        var caseStudyId = session['casestudy'];
        if (caseStudyId == null){
          document.getElementById('warning').style.display = 'block';
          return;
        }
        caseStudy = new CaseStudy({id: caseStudyId});
        activityGroups = new ActivityGroups({caseStudyId: caseStudyId});
        materials = new Materials();
        activities = new Activities({caseStudyId: caseStudyId});
        keyflows = new Keyflows({caseStudyId: caseStudyId});
        var loader = new Loader(document.getElementById('content'),
                                {disable: true});
        $.when(caseStudy.fetch(), activityGroups.fetch(), materials.fetch(), 
               keyflows.fetch(), activities.fetch()).then(function() {
          loader.remove();
          renderCaseStudy(caseStudy);
        });
    });
  });
});