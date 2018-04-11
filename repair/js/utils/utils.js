module.exports = {
    clearSelect: function(select, stop){
        var stop = stop || 0;
        for(var i = select.options.length - 1 ; i >= stop ; i--) { select.remove(i); }
    },

    formatCoords: function(c){
        return c[0].toFixed(2) + ', ' + c[1].toFixed(2);
    },
    
    // make tree out of list with children referencing to their parents by attribute
    //
    // options.parentAttr  name of attribute referencing to parent
    // options.relAttr  name of attribute the parentAttr references to
    treeify: function(list, options) {
        var options = options || {},
            treeList = [],
            lookup = {};
            
        var relAttr = options.relAttr || 'id',
            parentAttr = options.parentAttr || 'parent';
        list.forEach(function(item) {
            lookup[item[relAttr]] = item;
        });
        list.forEach(function(item) {
            if (item[parentAttr] != null) {
                lookupParent = lookup[item[parentAttr]]
                if (!lookupParent['nodes']) lookupParent['nodes'] = [];
                lookupParent['nodes'].push(item);
            } else {
                treeList.push(item);
            }
        });
        return treeList;
    },
    // success: function (data, textStatus, jqXHR)
    // error: function(response)
    uploadForm(data, url, options){
        var options = options || {},
            method = options.method || 'POST',
            success = options.success || function(){},
            error = options.error || function(){};
        var formData = new FormData();
        for (var key in data){
            if (data[key] instanceof Array){
                data[key].forEach(function(d){
                     formData.append(key, d);
                })
            }
            else
                formData.append(key, data[key]);
        }
        $.ajax({
            type: method,
            timeout: 50000,
            url: url,
            data: formData,
            cache: false,
            dataType: 'json',
            processData: false,
            contentType: false,
            success: success,
            error: error
        });
    },
    
    // model.markedForDeletion will be destroyed instead of uploaded
    queuedUpload(models, options){
        var options = options || {};
        
        // upload the models recursively (starting at index it)
        function uploadModel(models, it){
            // end recursion if no elements are left and call the passed success method
            if (it >= models.length) {
                if (options.success) options.success();
                return;
            };
            var model = models[it];
            // upload or destroy current model and upload next model recursively on success
            var params = {
                success: function(){ uploadModel(models, it+1) },
                error: options.error
            }
            if (model.markedForDeletion){
                // only already existing models can be destroyed (indicated by id)
                if (model.id) 
                    model.destroy(params);
                else uploadModel(models, it+1)
            }
            else {
                model.save(null, params);
            }
        };

        // start recursion at index 0
        uploadModel(models, 0);
    }
}