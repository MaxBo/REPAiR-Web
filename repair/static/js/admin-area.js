require(['./libs/domReady!', './require-config'], function (doc, config) {
  require(['app/models/casestudy', 'app/views/admin-flows',
           'app/views/admin-actors', 
           'app/collections/flows', 'app/collections/actors',
           'app/collections/keyflows', 'app/collections/materials',
           'app-config', 'app/loader'],
  function (CaseStudy, FlowsView, EditActorsView, Flows, 
            Actors, Keyflows, Materials,
            appConfig) {

    var caseStudy,
        keyflows,
        activities,
        materials;

    var flowsView,
        editActorsView;

    function renderFlows(keyflow){
      if (flowsView != null)
        flowsView.close();
      flowsView = new FlowsView({
        el: document.getElementById('flows-content'),
        template: 'flows-edit-template',
        model: keyflow,
        materials: materials
      });
    };
    
    function renderEditActors(caseStudy){
      if (editActorsView != null)
        editActorsView.close();

      // create casestudy-object and render view on it (data will be fetched in view)

      editActorsView = new EditActorsView({
        el: document.getElementById('actors-edit'),
        template: 'actors-edit-template',
        model: caseStudy,
        collection: new Actors({caseStudyId: caseStudy.id}),
        onUpload: function(){renderEditActors(caseStudy)}
      });
    };

    function render(caseStudy){
      var caseStudyId = caseStudy.id;
      var flowInner = _.template(document.getElementById('flows-template').innerHTML);
      var el = document.getElementById('flows-edit');
      el.innerHTML = flowInner({casestudy: caseStudy.get('name'),
                                keyflows: keyflows});

      var keyflowSelect = document.getElementById('flows-select');
      
      keyflowSelect.addEventListener('change', function(){
        var keyflow = keyflows.get(keyflowSelect.value);
        renderFlows(keyflow);
      });
      
      //// rerender view on data (aka sankey)
      //document.getElementById('refresh-dataview-btn').addEventListener(
        //'click', onKeyflowChange);
      //// rerender view on data-entries
      //document.getElementById('refresh-dataentry-btn').addEventListener(
        //'click', function(){renderDataEntry(caseStudy)});


      if (keyflows.length > 0){
        renderFlows(keyflows.first());
      }
      renderEditActors(caseStudy);
      
    }

    var session = appConfig.getSession(
      function(session){
        var caseStudyId = session['casestudy'];
        if (caseStudyId == null){
          document.getElementById('warning').style.display = 'block';
          return;
        }
        caseStudy = new CaseStudy({id: caseStudyId});
        materials = new Materials();
        keyflows = new Keyflows({caseStudyId: caseStudyId});
        var loader = new Loader(document.getElementById('content'),
                                {disable: true});
        $.when(caseStudy.fetch(), materials.fetch(), 
               keyflows.fetch()).then(function() {
          loader.remove();
          render(caseStudy);
        });
    });
  });
});