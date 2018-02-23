describe("Test", function() {

    require('../utils/overrides');
    var Actors = require('../collections/actors');
    var actors = new Actors([], {caseStudyId: 7, keyflowId: 30});
    // this doesn't work because it is asynchronous
    actors.fetch({
        success: function(){
            console.log(actors)
        }
    })
    
    //no tests yet
});
