
define(['app/models/casestudy', 'app/views/data-entry-flows',
        'app/views/data-entry-actors', 'app/views/data-entry-products', 
        'app/collections/flows', 'app/collections/actors',
        'app/collections/keyflows', 'app/collections/materials',
        'app-config', 'app/loader'],
function (CaseStudy, FlowsView, ActorsView, EditProductsView, Flows, 
          Actors, Keyflows, Materials,
          appConfig, Loader) {
  var _ = require('underscore');
  var caseStudy,
      keyflows,
      activities,
      materials;

  var flowsView,
      actorsView,
      editProductsView;
      
  var refreshFlowsBtn = document.getElementById('refresh-flowview-btn'),
      refreshProductsBtn = document.getElementById('refresh-productsview-btn'),
      refreshActorsBtn = document.getElementById('refresh-actorsview-btn');

  function renderFlows(keyflow){
    if (keyflow == null) return;
    if (flowsView != null)
      flowsView.close();
    flowsView = new FlowsView({
      el: document.getElementById('flows-content'),
      template: 'flows-edit-template',
      model: keyflow,
      materials: materials, 
      caseStudy: caseStudy
    });
    refreshFlowsBtn.style.display = 'block';
  };
  
  function renderEditActors(keyflow){
    if (keyflow == null) return;
    if (actorsView != null)
      actorsView.close();
    // create casestudy-object and render view on it (data will be fetched in view)

    actorsView = new ActorsView({
      el: document.getElementById('actors-content'),
      template: 'actors-template',
      model: keyflow,
      caseStudy: caseStudy,
      onUpload: function(){renderEditActors(keyflow)}
    });
    refreshActorsBtn.style.display = 'block';
  };
  
  function renderEditProducts(keyflow){
    if (keyflow == null) return;
    if (editProductsView != null)
      editProductsView.close();

    // create casestudy-object and render view on it (data will be fetched in view)

    editProductsView = new EditProductsView({
      el: document.getElementById('products-content'),
      template: 'products-edit-template',
      model: keyflow,
      caseStudy: caseStudy,
      materials: materials, 
      onUpload: function(){renderEditProducts(keyflow)}
    });
    refreshProductsBtn.style.display = 'block';
  };

  function render(caseStudy){

    var keyflowSelect = document.getElementById('keyflow-select');
    function getKeyflow(){
      return keyflows.get(keyflowSelect.value);
    }
    document.getElementById('keyflow-warning').style.display = 'block';
    keyflowSelect.addEventListener('change', function(){
      var keyflow = getKeyflow();
      document.getElementById('keyflow-warning').style.display = 'none';
      renderFlows(keyflow);
      renderEditActors(keyflow);
      renderEditProducts(keyflow);
    });
    refreshFlowsBtn.addEventListener('click', function(){renderFlows(getKeyflow())});
    refreshProductsBtn.addEventListener('click', function(){renderEditProducts(getKeyflow())});
    refreshActorsBtn.addEventListener('click', function(){renderEditActors(getKeyflow())});
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