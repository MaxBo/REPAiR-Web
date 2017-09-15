function toggleActive(id) {
    var div = document.getElementById(id);
    var className = div.getAttribute("class");
    console.log(div)
    
    if (className == 'active'){
         div.className = '';
     } else {
         div.className = 'active';
     }
}