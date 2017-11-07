function Loader (parent) {
  var div = document.createElement('div');
  div.className = 'loader';
  parent.appendChild(div);

  this.remove = function(){
    parent.removeChild(div);
  }
};