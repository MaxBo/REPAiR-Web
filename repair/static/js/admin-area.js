require(['./libs/domReady!', './app'], function (doc, app) {

    var deactivateTabs = function(){
        var tabs = document.querySelectorAll('.admin-tab');
        console.log(tabs);
        tabs.forEach(function(tab) {
            tab.classList.remove('active');
        });
    }
    
    document.getElementById('enter-data-btn').addEventListener(
        'click', function(){
            deactivateTabs();
            var tab =  document.getElementById('activity-groups-edit');
            tab.classList.add('active');
        });

    document.getElementById('view-data-btn').addEventListener(
        'click', function(){
            deactivateTabs();
            var tab =  document.getElementById('sankey');
            tab.classList.add('active');
        });

    requirejs(['app/admin-data-tree']);
});