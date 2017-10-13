require(['./libs/domReady!', './config'], function (doc, config) {
    require(['jquery', 'app/collections/CaseStudies', 'app/models/Stakeholder', 
            'app/collections/Stakeholders', 'app/visualizations/sankey',
            'app/admin-data-tree'], 
    function ($, CaseStudies, Stakeholder, Stakeholders, Sankey, DataTree) {
    
        /*
        var stakeholders = new Stakeholders();
        stakeholders.fetch({success: function(){
            console.log(stakeholders);
        }});
        var caseStudies = new CaseStudies();
        caseStudies.fetch({success: function(){
            console.log(caseStudies);
        }});
        var stakeholder = new Stakeholder({name: 'bla'});
        console.log(stakeholder);
        //stakeholder.save()*/
        
        // ToDo: fetch real data when models are implemented
        function generateRandomData() {
          var dataObject = new Object();
        
          var mostNodes = 20;
          var mostLinks = 40;
          var numNodes = Math.floor((Math.random()*mostNodes)+1);
          var numLinks = Math.floor((Math.random()*mostLinks)+1);
        
          // Generate nodes
          dataObject.nodes = new Array();
          for( var n = 0; n < numNodes; n++ ) {
            var node = new Object();
                node.name = "Node-" + n;
            dataObject.nodes[n] = node;
          }
        
          // Generate links
          dataObject.links = new Array();
          for( var i = 0; i < numLinks; i++ ) {
            var link = new Object();
                link.target = link.source = Math.floor((Math.random()*numNodes));
                while( link.source === link.target ) { link.target = Math.floor((Math.random()*numNodes)); }
                link.value = Math.floor((Math.random() * 100) + 1);
        
            dataObject.links[i] = link;
          }
        
          return dataObject;
        }
        
        // ToDo: make a view out of this?
        function renderSankey(){
            var sankey = new Sankey({
                height: 600,
                divid: '#sankey',
                title: 'D3 Sankey with cycle-support (random data, new data on click on "Refresh"-button)'
            })
            var randomData = generateRandomData();
            sankey.render(randomData);
        };
        
        var deactivateTabs = function(cls){
            var tabs = document.querySelectorAll(cls);
            tabs.forEach(function(tab) {
                tab.classList.remove('active');
            });
        }
        
        var activate = function(tabId){
            var tab =  document.getElementById(tabId);
            tab.classList.add('active');
            //tab.style.display = 'block';
        }
        
        var onClick = function(link){
            var tag = link.tag;
            deactivateTabs('.admin-tab');
            // ToDo: emit click
            //activate('data-entry');
            if (tag == 'activity') { activate('activity-edit') }
            else if (tag == 'activity-group') { activate('activity-group-edit') }
            else if (tag == 'actor') { activate('actor-edit') };
        }
        
        var dataTree = new DataTree({divid: '#data-tree', onClick: onClick})
            
        document.getElementById('balance-verify-button-group').style.display = 'none';
        document.getElementById('balance-verify-single').style.display = 'none';
        
        
        
        //document.getElementById('data-tree-group').style.display = 'none';
    
        
        //document.getElementById('enter-data-btn').addEventListener(
            //'click', function(){
                //deactivateTabs();
                //var tab =  document.getElementById('activity-groups-edit');
                //tab.classList.add('active');
                //document.getElementById('data-tree-group').style.display = 'block';
            //});
    
        //document.getElementById('view-data-btn').addEventListener(
            //'click', function(){
                //deactivateTabs();
                //var tab =  document.getElementById('sankey');
                //tab.classList.add('active');
                //document.getElementById('data-tree-group').style.display = 'none';
                
                //renderSankey();
            //});
        renderSankey();
        document.getElementById('refresh-view-btn').addEventListener(
            'click', function(){
                renderSankey();
        });
        
     });
});