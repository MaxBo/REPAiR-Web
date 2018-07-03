define([], function()
{
    /**
    * Class to fetch/save attributes stored in current session
    * @author Christoph Franke
    */
    class Session {

        /**
        * create a session object
        *
        * @param {Object} options
        * @param {string} [options.url='/session']        backend route to session
        *
        */
        constructor(options){
            var options = options || {};
            this.url = options.url || '/session';
            this.attributes = {};
        }

        /**
        * callback for session
        *
        * @callback module:utils/Session~success
        * @param {Object} session - fetched session object (=this)
        */

        /**
        * fetch the current session object from the server
        *
        * @param {module:utils/Session~success=} options.success - called when session object is successfully fetched
        *
        * @method getSession
        * @memberof module:config
        */
        fetch(options){
            var _this = this;
            function success(json){
                _this.attributes = {};
                for (var key in json) {
                    _this.attributes[key] = json[key];
                }
                if (options.success){
                    options.success(_this);
                }
            }
            fetch(this.url, {
                headers: {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'include'
            }).then(response => response.json()).then(json => success(json));
        }
        
        get(attribute){
            return this.attributes[attribute];
        }
        
        set(attribute, value){
            this.attributes[attribute] = value;
        }
        
        save(options){
            
        }

    };


    return Session;
});
