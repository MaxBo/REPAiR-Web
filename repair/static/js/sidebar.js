function toggleActive(id) {
    var div = document.getElementById(id);
    var className = div.getAttribute("class");
    console.log(div)
    
    if (className == 'active'){
        div.className = '';
    } else {
        div.className = 'active';
    }
     
    $('#sidebar > .sidebar-nav > li').hover(function () {
        $(this).find('.sidebar-nav').show(500);
    }, function () {
        $(this).find('.sidebar-nav').hide(500);
    });
}