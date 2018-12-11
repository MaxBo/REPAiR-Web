
define(['underscore','views/common/baseview', 'collections/gdsecollection'],

function(_, BaseView, GDSECollection, Muuri){
    /**
    *
    * @author Christoph Franke
    * @name module:views/ObjectivesView
    * @augments Backbone.View
    */
    var ObjectivesView = BaseView.extend(
        /** @lends module:views/ObjectivesView.prototype */
    {

        /**
        * render workshop view on overall objective-ranking by involved users
        *
        * @param {Object} options
        * @param {HTMLElement} options.el                      element the view will be rendered in
        * @param {string} options.template                     id of the script element containing the underscore template to render this view
        * @param {module:models/CaseStudy} options.caseStudy   the casestudy of the keyflow
        * @param {module:models/CaseStudy} options.keyflowId   the keyflow the objectives belong to
        *
        * @constructs
        * @see http://backbonejs.org/#View
        */
        initialize: function(options){
            ObjectivesView.__super__.initialize.apply(this, [options]);
            var _this = this;
            this.template = options.template;
            this.caseStudy = options.caseStudy;
            this.aims = options.aims;
            this.objectives = options.objectives;
            this.keyflowId = options.keyflowId;
            this.keyflowName = options.keyflowName;

            console.log(this.objectives)
            this.users = options.users.filterBy({'gets_evaluated' : true})

            this.render();
        },
        /*
        * render the view
        */
        render: function(){
            var _this = this,
                html = document.getElementById(this.template).innerHTML,
                template = _.template(html);
            this.el.innerHTML = template({ keyflowName: this.keyflowName });
            this.table = this.el.querySelector('#objectives-table');
            var header = this.table.createTHead().insertRow(0);
            header.appendChild(document.createElement('th'));
            var rankingMap = {},
                cellUsers = [],
                avgRankings = {};
            this.users.forEach(function(user){
                var name = user.get('alias') || user.get('name'),
                    th = document.createElement('th');
                cellUsers.push(user.id);
                th.innerHTML = name;
                header.appendChild(th);
                var userObjectives = _this.objectives.filterBy({'user': user.get('user')});
                userObjectives.comparator = 'priority';
                userObjectives.sort();
                // normalize priorities into a ranking from 1 ascending
                var i = 1;
                userObjectives.forEach(function(userObj){
                    var aimId = userObj.get('aim'),
                        aimRank = rankingMap[aimId];
                    // aim was not considered yet
                    if (!aimRank) {
                        aimRank = rankingMap[aimId] = {};
                        avgRankings[aimId] = 0;
                    }
                    aimRank[user.id] = i;
                    avgRankings[aimId] += i;
                    i++;
                })
            })

            // sort aims by average ranking
            var sortRank = [];
            for (var aimId in avgRankings) {
                sortRank.push([aimId, avgRankings[aimId]]);
            }
            sortRank.sort(function(a, b) {
                return a[1] - b[1];
            });

            // fill table with sorted aims and individual ranks
            sortRank.forEach(function(sortedAim){
                var aim = _this.aims.get(sortedAim[0]),
                    row = _this.table.insertRow(-1);
                row.insertCell(0).innerHTML = aim.get('text');
                var aimRank = rankingMap[aim.id];
                cellUsers.forEach(function(userId){
                    var cell = row.insertCell(-1),
                        rank = aimRank[userId];
                    if (rank) cell.innerHTML = '#' + rank;
                });

            })
        },
    });
    return ObjectivesView;
}
);

