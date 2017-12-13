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
        el: document.getElementById('flows-edit'),
        template: 'flows-edit-template',
        model: keyflow,
        materials: materials, 
        caseStudy: caseStudy
      });
    };
    
    function renderEditActors(keyflow){
      if (editActorsView != null)
        editActorsView.close();

      // create casestudy-object and render view on it (data will be fetched in view)

      editActorsView = new EditActorsView({
        el: document.getElementById('actors-edit'),
        template: 'actors-edit-template',
        model: keyflow,
        caseStudy: caseStudy,
        onUpload: function(){renderEditActors(keyflow)}
      });
    };

    function render(caseStudy){

      var keyflowSelect = document.getElementById('keyflow-select');
      document.getElementById('keyflow-warning').style.display = 'block';
      keyflowSelect.addEventListener('change', function(){
        var keyflow = keyflows.get(keyflowSelect.value);
        document.getElementById('keyflow-warning').style.display = 'none';
        renderFlows(keyflow);
        renderEditActors(keyflow);
      });
      document.getElementById('keyflow-select').disabled = false;
    }

    var session = appConfig.getSession(
      function(session){
        var caseStudyId = session['casestudy'];
        if (caseStudyId == null){
          document.getElementById('casestudy-warning').style.display = 'block';
          document.getElementById('keyflow-warning').style.display = 'none';
          return;
        }
        caseStudy = new CaseStudy({id: caseStudyId});
        materials = new Materials();
        keyflows = new Keyflows([], {caseStudyId: caseStudyId});
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