define(['browser-cookies'], function(cookies)
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
        */
        fetch(options){
            var _this = this;
            function success(json){
                _this.setAttributes(json);
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

        switchCaseStudy(caseStudyId, options){
            var options = options || {};
            console.log(options)
            $.ajax({
                type: "POST",
                url: this.url,
                data: {
                    casestudy: caseStudyId,
                    //next: '/status-quo'
                },
                success: options.success,
                error: options.error
            });
        }

        setAttributes(json){
            this.attributes = {};
            for (var key in json) {
                this.attributes[key] = json[key];
            }
        }

        /**
        * get value of attribute by name
        *
        * @param {string} attribute - name of the attribute
        * @returns {string}
        */
        get(attribute){
            return this.attributes[attribute];
        }

        /**
        * set attribute
        *
        * @param {string} attribute - name of the attribute
        * @param {string} value - value of attribute to set
        */
        set(attribute, value){
            this.attributes[attribute] = value;
        }

        /**
        * save the current session object from the server
        *
        * @param {Object} [attributes] - attributes to save, if null is passed all attributes will be uploaded
        * @param {module:utils/Session~success=} options.success - called when session object is successfully saved
        * @param {module:utils/Session~error=} options.error - called when upload did not succeed
        *
        */
        save(attributes, options){
            var _this = this,
                options = options || {};
            function success(json){
                _this.setAttributes(json);
                if (options.success){
                    options.success(_this);
                }
            };
            var attributes = attributes || this.attributes,
                csrftoken = cookies.get('csrftoken');
            fetch(this.url, {
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                method: 'post',
                body: JSON.stringify(attributes),
                credentials: 'include'
            }).then(response => success(response));
        }

    };

    return Session;
});
