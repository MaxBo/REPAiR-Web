define(['document-ready', 'bootstrap', 'utils/overrides'],
function (ready) {  
  /**
   * EITHER LOAD THIS IN TEMPLATE OR MAKE AN OWN ENTRY POINT IMPORTING THIS!!!!
   *
   * base entry point loading requirements for base django template and overriding functions as needed by other entry points
   *
   * @author Christoph Franke
   * @module Base
   */
   
   ready(function(){
    // hide sidebar if there is no content in it
     if (document.getElementById('sidebar-content').childElementCount == 0){
       document.getElementById('wrapper').style.paddingLeft = '0px';
     }
     else 
       document.getElementById('sidebar-wrapper').style.display = 'inline';
     
     function toggleShow(element){
       closeDropdowns();
       element.classList.toggle('show');
     }
     
     function closeDropdowns(){
       var dropdowns = document.getElementsByClassName("dropdown-content");
       var i;
       for (i = 0; i < dropdowns.length; i++) {
         var openDropdown = dropdowns[i];
         if (openDropdown.classList.contains('show')) {
           openDropdown.classList.remove('show');
         }
       }
     }
     
     // show content on dropdown button click (for all dropdowns)
     dropdowns = [].slice.call(document.querySelectorAll('.dropdown'));
     
     dropdowns.forEach(function(dropdown) {
       var button = dropdown.querySelector('.dropdown-button'),
           content = dropdown.querySelector('.dropdown-content');
       button.addEventListener('click', function(){ toggleShow(content) })
     });
     
     // Close the dropdowns if the user clicks outside of it
     window.onclick = function(event) {
       if (!event.target.matches('.dropdown-button')) closeDropdowns();
     }
  });
 });