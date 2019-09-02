define(['underscore','views/common/baseview', 'collections/gdsecollection',
        'html2canvas', 'viewerjs', 'viewerjs/dist/viewer.css'],

function(_, BaseView, GDSECollection, html2canvas, Viewer){

    function html2image(container, onSuccess){
        html2canvas(container).then(canvas => {
            var data = canvas.toDataURL("image/png");
            onSuccess(data);
        });
    };

    /**
    *
    * @author Christoph Franke
    * @name module:views/ConclusionsView
    * @augments Backbone.View
    */
    var ConclusionsView = BaseView.extend(
        /** @lends module:views/ConclusionsView.prototype */
        {

        /**
        * render setup view on challenges and aims
        *
        * @param {Object} options
        * @param {HTMLElement} options.el                          element the view will be rendered in
        * @param {string} options.template                         id of the script element containing the underscore template to render this view
        * @param {module:models/CaseStudy} options.caseStudy       the casestudy to add challenges and aims to
        *
        * @constructs
        * @see http://backbonejs.org/#View
        */
        initialize: function(options){
            ConclusionsView.__super__.initialize.apply(this, [options]);
            var _this = this;

            this.consensusLevels = options.consensusLevels;
            this.sections = options.sections;
            this.keyflows = options.keyflows;
            this.caseStudy = options.caseStudy;
            this.conclusionsInCasestudy = {};
            var promises = [];
            this.loader.activate();
            this.keyflows.forEach(function(keyflow){
                var conclusions = new GDSECollection([], {
                    apiTag: 'conclusions',
                    apiIds: [_this.caseStudy.id, keyflow.id]
                });
                _this.conclusionsInCasestudy[keyflow.id] = conclusions;
                promises.push(conclusions.fetch({error: alert}));
            })
            Promise.all(promises).then(function(){
                _this.render();
                _this.loader.deactivate();
            })
        },

        /*
        * dom events (managed by jquery)
        */
        events: {
            //'click .add-challenge-button': 'addChallenge',
        },

        addConclusion: function(keyflowId){
            var html = document.getElementById('add-conclusion-template').innerHTML,
                template = _.template(html),
                content = document.getElementById('content'),
                _this = this;

            function upload(conclusion){

                //conclusionsInCasestudy[keyflow.id].create()
            }

            if (!this.addModal) {
                this.addModal = document.getElementById('add-conclusion-modal');
                $(this.addModal).on('shown.bs.modal', function() {
                    new Viewer.default(_this.addModal.querySelector('img'));
                });
            }

            html2image(content, function(image){
                _this.addModal.innerHTML = template({
                    consensusLevels: _this.consensusLevels,
                    sections: _this.sections,
                    image: image
                });
                $(_this.addModal).modal('show');

                _this.addModal.querySelector('.btn.confirm').addEventListener('click', function(){
                    console.log('click')
                    var step = content.querySelector('.tab-pane.active').dataset.step,
                        conclusions = _this.conclusionsInCasestudy[keyflowId];
                    conclusions.create({
                        "consensus_level": _this.addModal.querySelector('select[name="consensus"]').value,
                        "section": _this.addModal.querySelector('select[name="section"]').value,
                        "step": step,
                        "text": _this.addModal.querySelector('textarea[name="comment"]').value,
                        //"image": ,
                    }, {
                        wait: true,
                        success: function(){
                            _this.addModal.close();
                        },
                        error: function(arg1, arg2){
                            var response = (arg1.status) ? arg1 : arg2;
                            if (response.responseText)
                                alert(response.responseText);
                            else
                                alert(response.statusText);
                        }
                    })
                })
            })
        },

        /*
        * render the view
        */
        render: function(){
            var _this = this,
                html = document.getElementById(this.template).innerHTML,
                template = _.template(html);
            this.el.innerHTML = template();
        }
    });
    return ConclusionsView;
}
);

