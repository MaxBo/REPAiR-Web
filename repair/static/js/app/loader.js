function Loader (parent) {
  var div = document.createElement('div');
  div.className = 'loader';
  parent.appendChild(div);

  this.remove = function(){
    try{
      parent.removeChild(div);
    }
    catch(err){
      console.log(err.message)
    }
  }
};