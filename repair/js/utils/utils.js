/**
* utility functions for frontend scripts
* @author Christoph Franke
*/
function log10(val) {
  return Math.log(val) / Math.LN10;
}

var color = d3.scale.category20();
module.exports = {

    removeEventListeners: function(el) {
        var clone = el.cloneNode(true);
        el.parentNode.replaceChild(clone, el);
        return clone;
    },

    logNormalize: function(value, minValue, maxValue, min, max) {
        if (value == minValue) return min;
        var mx = (Math.log2((value - minValue)) / (Math.log2(maxValue - minValue))),
            preshiftNormalized = mx * (max - min),
            shiftedNormalized = preshiftNormalized + min;
        return shiftedNormalized;
    },

    colorByName: function(name){
        name = String(name);
        return color(name.replace(/ .*/, ""));
    },

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
                lookupParent = lookup[item[parentAttr]];
                if (lookupParent != null){
                    if (!lookupParent['nodes']) lookupParent['nodes'] = [];
                    lookupParent['nodes'].push(item);
                }
            } else {
                treeList.push(item);
            }
        });
        return treeList;
    },
    // success: function (data, textStatus, jqXHR)
    // error: function(response)
    uploadForm: function(data, url, options){
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
            timeout: 3600000,
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
    queuedUpload: function(models, options){
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
    },

    // loader shown in center of given div as spinning circle when activated
    // options.disable disables given div while loader is active
    Loader: function(div, options) {
        var loaderDiv = document.createElement('div');
        loaderDiv.className = 'loader';

        this.activate = function(opt){
            var opt = opt || {};
            loaderDiv.style.top = null;
            if (options != null && options.disable)
                div.classList.add('disabled');
            if (opt.offsetX != null) loaderDiv.style.top = opt.offsetX;
            div.appendChild(loaderDiv);
        }

        this.deactivate = function(){
            if (options != null && options.disable)
                div.classList.remove('disabled');
            try{
                div.removeChild(loaderDiv);
            }
            catch(err){
                console.log(err.message)
            }
        }
    },
    range: function(start, end, step) {
        const len = Math.floor((end - start) / step) + 1
        return Array(len).fill().map((_, idx) => start + (idx * step))
    },

    // checks given flows and adds and fetches missing models to origins and destinations
    // calls success() after completion
    complementFlowData: function(flows, origins, destinations, success){
        var GDSECollection = require('collections/gdsecollection');
        var originIds = origins.pluck('id'),
            destinationIds = destinations.pluck('id'),
            missingOriginIds = new Set(),
            missingDestinationIds = new Set();
        // clone to avoid manipulating the original collection
        origins = new GDSECollection(origins.toJSON(), {
            apiTag: origins.apiTag, apiIds: origins.apiIds
        })
        destinations = new GDSECollection(destinations.toJSON(), {
            apiTag: destinations.apiTag, apiIds: destinations.apiIds
        })
        flows.forEach(function(flow){
            var origin = flow.get('origin'),
                destination = flow.get('destination');
            if(!originIds.includes(origin)) missingOriginIds.add(origin);
            if(!destinationIds.includes(destination)) missingDestinationIds.add(destination);
        })
        var promises = [];
        // WARNING: postfetch works only with filter actors route, should be
        // fetched in case of groups and activities, but in fact they should
        // be complete
        if (missingOriginIds.size > 0){
            var missingOrigins = new GDSECollection([], {
                url: origins.url()
            })
            promises.push(missingOrigins.postfetch({
                body: { 'id': Array.from(missingOriginIds).join() },
                success: function(){
                    origins.add(missingOrigins.toJSON(), {silent: true});
                }
            }))
        }
        if (missingDestinationIds.size > 0){
            var missingDestinations = new GDSECollection([], {
                url: destinations.url()
            })
            promises.push(missingDestinations.postfetch({
                body: { 'id': Array.from(missingDestinationIds).join() },
                success: function(){
                    destinations.add(missingDestinations.toJSON(), {silent: true});
                }
            }))
        }

        Promise.all(promises).then(function(){
            success(origins, destinations);
        })
    }
}
