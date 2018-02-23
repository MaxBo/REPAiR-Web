describe("Player", function() {

  
  //var login = function(callback){
      //var request = new XMLHttpRequest();
      //var url = '/login/login/';
      ////var url = this.url + '/wfs?Request=GetCapabilities';
      //request.open('POST', url, true);
      //request.setRequestHeader("Content-type", "application/json");
      
      //function processRequest(e) {
        //console.log(e)
        //console.log(request.status)
        //console.log(request.responseText)
        //callback()
      //}
      //request.onreadystatechange = processRequest;
      //request.send({ username: 'admin', password: 'S_fmK10yB$7e' }); 
    //}
  
  require('jquery');
  //$.get( "/home/").done(function( data ) {
    //var cookies = require('browser-cookies');
    //var csrftoken = cookies.get('csrftoken');
    //console.log(csrftoken);
  //});
    
  var testActors = function(){
    require('../../repair/js/utils/overrides');
    var Actors = require('../../repair/js/collections/actors');
    var actors = new Actors([], {caseStudyId: 7, keyflowId: 30});
    actors.fetch({
      success: function(){
        console.log(actors)
      }
  })}
  
  $.post( "/login/login/", { username: 'admin', password: 'S_fmK10yB$7e' } ).done(function( data ) {
    alert( "Data Loaded: " + data );
    
    testActors()
  });

});
