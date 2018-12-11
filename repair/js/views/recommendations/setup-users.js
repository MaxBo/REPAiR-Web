define(['views/common/baseview', 'underscore', 'collections/gdsecollection/'],

function(BaseView, _, GDSECollection){
/**
*
* @author Christoph Franke
* @name module:views/SetupUsersView
* @augments  module:views/BaseView
*/
var SetupUsersView = BaseView.extend(
    /** @lends module:views/SetupUsersView.prototype */
{

    initialize: function(options){
        SetupUsersView.__super__.initialize.apply(this, [options]);
        _.bindAll(this, 'addUserRow');

        this.caseStudy = options.caseStudy;
        this.users = new GDSECollection([], {
            apiTag: 'usersInCasestudy',
            apiIds: [this.caseStudy.id]
        });
        this.users.fetch({
            success: this.render,
            error: this.onError
        })
    },

    render: function(){
        this.users.forEach(this.addUserRow)
    },

    addUserRow: function(user){
        var table = document.getElementById('user-table'),
            row = table.insertRow(-1),
            _this = this;

        row.insertCell(0).innerHTML = user.get('name');

        var aliasInput = document.createElement('input');
        aliasInput.style.width = '90%';
        row.insertCell(1).appendChild(aliasInput);
        aliasInput.value = user.get('alias');

        var evaCheck = document.createElement('input');
        evaCheck.type = 'checkbox';
        row.insertCell(2).appendChild(evaCheck);
        evaCheck.checked = user.get('gets_evaluated');

        aliasInput.addEventListener('change', function(){
            var alias = this.value;
            user.save(
                { alias: alias },
                { patch: true, error: _this.onError }
            )
        })

        evaCheck.addEventListener('change', function(){
            var in_eva = this.checked;
            user.save(
                { gets_evaluated: in_eva },
                { patch: true, error: _this.onError }
            )
        })
    }

});
return SetupUsersView;
}
);

