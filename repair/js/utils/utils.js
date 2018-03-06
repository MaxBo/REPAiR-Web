module.exports = {
    clearSelect: function(select, stop){
        var stop = stop || 0;
        for(var i = select.options.length - 1 ; i >= stop ; i--) { select.remove(i); }
    },

    formatCoords: function(c){
        return c[0].toFixed(2) + ', ' + c[1].toFixed(2);
    }
}