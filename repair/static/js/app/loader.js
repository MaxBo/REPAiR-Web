function Loader (div, options) {
  if (options != null && options.disable)
    div.classList.toggle('disabled');
  var loaderDiv = document.createElement('div');
  loaderDiv.className = 'loader';
  div.appendChild(loaderDiv);

  this.remove = function(){
    if (options != null && options.disable)
      div.classList.toggle('disabled');
    try{
      div.removeChild(loaderDiv);
    }
    catch(err){
      console.log(err.message)
    }
  }
};