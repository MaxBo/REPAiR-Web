define(['underscore','views/common/baseview', 'collections/gdsecollection',
        'models/gdsemodel', 'html2canvas', 'muuri', 'viewerjs', 'viewerjs/dist/viewer.css'],

function(_, BaseView, GDSECollection, GDSEModel, html2canvas, Muuri, Viewer){

    function html2image(container, onSuccess){
        html2canvas(container).then(canvas => {
            var data = canvas.toDataURL("image/png");
            onSuccess(data);
        });
    };

    // source: https://stackoverflow.com/questions/16968945/convert-base64-png-data-to-javascript-file-objects
    function dataURLtoFile(dataurl, filename) {
        var arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)[1],
            bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
        while(n--){
            u8arr[n] = bstr.charCodeAt(n);
        }
        return new File([u8arr], filename, {type:mime});
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

            if (!this.addModal) {
                this.addModal = document.getElementById('add-conclusion-modal');
                $(this.addModal).on('shown.bs.modal', function() {
                    new Viewer.default(_this.addModal.querySelector('img'));
                });
            }

            html2image(content, function(dataURL){
                _this.addModal.innerHTML = template({
                    consensusLevels: _this.consensusLevels,
                    sections: _this.sections,
                    image: dataURL
                });
                $(_this.addModal).modal('show');

                _this.addModal.querySelector('.btn.confirm').addEventListener('click', function(){
                    var step = content.querySelector('.tab-pane.active').dataset.step,
                        conclusions = _this.conclusionsInCasestudy[keyflowId];

                    var data = {
                        "consensus_level": _this.addModal.querySelector('select[name="consensus"]').value,
                        "section": _this.addModal.querySelector('select[name="section"]').value,
                        "step": step,
                        "text": _this.addModal.querySelector('textarea[name="comment"]').value
                    }

                    var image = dataURLtoFile(dataURL, 'screenshot.png');
                    if (_this.addModal.querySelector('input[name="screenshot"]').checked) {
                        data.image = image;
                    }

                    var conclusion = new GDSEModel( {}, { apiTag: 'conclusions', apiIds: [ _this.caseStudy.id, keyflowId ] });
                    conclusion.save(data, {
                        success: function(){
                            conclusions.add(conclusion);
                            //$(_this.addModal).modal('close');
                            var grid = _this.grids[keyflowId][conclusion.get('consensus_level')];
                            _this.addConclusionItem(grid, conclusion);
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
            this.el.innerHTML = template({
                keyflows: this.keyflows,
                consensusLevels: this.consensusLevels
            });
            _this.grids = {};
            //this.level1Select = this.el.querySelector('select[name="sort-level-1"]');
            //this.level2Select = this.el.querySelector('select[name="sort-level-2"]');
            //this.level3Select = this.el.querySelector('select[name="sort-level-3"]');
            //function fillSort(select, i){
                //var labels = ['keyflow', 'consensus level', 'section', 'GDSE step'];
                //labels.forEach(function(label){
                    //var option = document.createElement('option');
                    //option.innerHTML = label;
                    //select.appendChild(option);
                //})
                //select.selectedIndex = i;
            //}
            //fillSort(this.level1Select, 0);
            //fillSort(this.level2Select, 1);
            //fillSort(this.level3Select, 2);
            this.keyflows.forEach(function(keyflow){
                var keyflowPanel = _this.el.querySelector('#keyflow-' + keyflow.id),
                    conclusions = _this.conclusionsInCasestudy[keyflow.id];
                _this.grids[keyflow.id] = {};
                _this.consensusLevels.forEach(function(level){
                    var levelPanel = keyflowPanel.querySelector('.item-panel[data-level="' + level.id + '"]')
                    _this.grids[keyflow.id][level.id] = new Muuri(levelPanel, {
                        items: '.conclusion-item',
                        dragAxis: 'y',
                        layoutDuration: 400,
                        layoutEasing: 'ease',
                        dragEnabled: true,
                        dragSortInterval: 0,
                        dragReleaseDuration: 400,
                        dragReleaseEasing: 'ease'
                    });
                })
                conclusions.forEach(function(conclusion){
                    var level = conclusion.get('consensus_level'),
                        panel = keyflowPanel.querySelector('.item-panel[data-level="' + level + '"]'),
                        grid = _this.grids[keyflow.id][level];
                    _this.addConclusionItem(grid, conclusion);
                })
            })
        },

        addConclusionItem: function(grid, conclusion){
            var _this = this,
                item = document.createElement('div'),
                html = document.getElementById('conclusion-item-template').innerHTML,
                template = _.template(html);
            item.innerHTML = template({
                conclusion: conclusion,
                section: this.sections.get(conclusion.get('section')).get('name')
            });
            item.classList.add('conclusion-item', 'draggable', 'raised');
            item.style.position = 'absolute';
            item.style.height = '100px';
            grid.add(item);
            new Viewer.default(item);

            item.querySelector('button[name="remove"]').addEventListener('click', function(){
                var message = gettext('Do you really want to delete the conclusion?');
                _this.confirm({ message: message, onConfirm: function(){
                    conclusion.destroy({
                        success: function() { grid.remove(item, { removeElements: true }); },
                        error: _this.onError,
                        wait: true
                    })
                }});
            })
        }

    });
    return ConclusionsView;
}
);

