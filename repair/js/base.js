define(['jquery', 'document-ready', 'bootstrap', 'utils/overrides'],
function ($, ready) {  
  /**
   *
   * base entry point loading requirements for base django template and overriding functions as needed by other entry points
   * sets up sidebar and dropdowns in base django template
   *
   * @author Christoph Franke
   * @module Base
   */
   
  ready(function () {
  
   // hide sidebar if there is no content in it
    if (document.getElementById('sidebar-content').childElementCount == 0){
      document.getElementById('wrapper').style.paddingLeft = '0px';
      document.getElementById('sidebar-wrapper').style.display = 'none';
      //console.log(document.getElementById('sidebar-wrapper'))
    };
    
    <!-- show/hide dropdown-menus in main menu on click -->
    
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
      console.log(content)
      button.addEventListener('click', function(){ toggleShow(content) })
    });
    
    // Close the dropdowns if the user clicks outside of it
    window.onclick = function(event) {
      if (!event.target.matches('.dropdown-button')) closeDropdowns();
    }
   });
 });