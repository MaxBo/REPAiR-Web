define(['utils/session'],
function (Session) {

    /**
    * global configuration file
    * @module config
    *
    * @author Christoph Franke
    */
    var config = {
        URL: '/' // base application URL
    };

    config.session = new Session();


    config.views = {
        layerproxy: '/proxy/layers/{0}/wms',
    }

    /** urls to resources in api
    * @name api
    * @memberof module:config
    */
    config.api = {
        base:                   '/api', // base Rest-API URL
        casestudies:            '/api/casestudies/',
        publications:           '/api/publications/',
        publicationsInCasestudy:'/api/casestudies/{0}/publications/',
        keyflows:               '/api/keyflows/',
        qualities:              '/api/qualities/',
        reasons:                '/api/reasons/',
        targets:                '/api/casestudies/{0}/aims/{1}/targets',
        targetvalues:           '/api/targetvalues',
        targetspatialreference: '/api/targetspecialreference/',
        areasOfProtection:      '/api/areasofprotection/',
        impactcategories:       '/api/impactcategories/',
        units:                  '/api/units/',
        usersInCasestudy:       '/api/casestudies/{0}/users',
        challenges:             '/api/casestudies/{0}/challenges',
        aims:                   '/api/casestudies/{0}/aims',
        consensusLevels:        '/api/casestudies/{0}/consensuslevels',
        sections:               '/api/casestudies/{0}/sections',
        userObjectives:         '/api/casestudies/{0}/userobjectives',
        flowTargets:            '/api/casestudies/{0}/userobjectives/{1}/flowtargets',
        chartCategories:        '/api/casestudies/{0}/chartcategories/',
        charts:                 '/api/casestudies/{0}/chartcategories/{1}/charts/',
        stakeholderCategories:  '/api/casestudies/{0}/stakeholdercategories/',
        stakeholders:           '/api/casestudies/{0}/stakeholdercategories/{1}/stakeholders/',
        solutionCategories:     '/api/casestudies/{0}/keyflows/{1}/solutioncategories/',
        solutions:              '/api/casestudies/{0}/keyflows/{1}/solutioncategories/{2}/solutions/',
        solutionQuantities:     '/api/casestudies/{0}/keyflows/{1}/solutioncategories/{2}/solutions/{3}/solutionquantities',
        solutionRatioOneUnits:  '/api/casestudies/{0}/keyflows/{1}/solutioncategories/{2}/solutions/{3}/solutionratiooneunits',
        strategies:             '/api/casestudies/{0}/keyflows/{1}/strategies/',
        solutionsInStrategy:    '/api/casestudies/{0}/keyflows/{1}/strategies/{2}/solutions/',
        quantitiesInImplementedSolution: '/api/casestudies/{0}/keyflows/{1}/strategies/{2}/solutions/{3}/quantities',
        layerCategories:        '/api/casestudies/{0}/layercategories',
        layers:                 '/api/casestudies/{0}/layercategories/{1}/layers',
        keyflowsInCaseStudy:    '/api/casestudies/{0}/keyflows',
        activitygroups:         '/api/casestudies/{0}/keyflows/{1}/activitygroups/',
        activities:             '/api/casestudies/{0}/keyflows/{1}/activities/',
        actors:                 '/api/casestudies/{0}/keyflows/{1}/actors/',
        adminLocations:         '/api/casestudies/{0}/keyflows/{1}/administrativelocations/',
        opLocations:            '/api/casestudies/{0}/keyflows/{1}/operationallocations/',
        products:               '/api/casestudies/{0}/keyflows/{1}/products/',
        wastes:                 '/api/casestudies/{0}/keyflows/{1}/wastes/',
        materials:              '/api/casestudies/{0}/keyflows/{1}/materials/',
        activityToActivity:     '/api/casestudies/{0}/keyflows/{1}/activity2activity/',
        groupToGroup:           '/api/casestudies/{0}/keyflows/{1}/group2group/',
        actorToActor:           '/api/casestudies/{0}/keyflows/{1}/actor2actor/',
        groupStock:             '/api/casestudies/{0}/keyflows/{1}/groupstock/',
        activityStock:          '/api/casestudies/{0}/keyflows/{1}/activitystock/',
        actorStock:             '/api/casestudies/{0}/keyflows/{1}/actorstock/',
        flowIndicators:         '/api/casestudies/{0}/keyflows/{1}/flowindicators/',
        flowFilters:            '/api/casestudies/{0}/keyflows/{1}/flowfilters/',
        arealevels:             '/api/casestudies/{0}/levels/',
        allareas:               '/api/casestudies/{0}/areas/',
        areas:                  '/api/casestudies/{0}/levels/{1}/areas/',
        wmsresources:           '/api/casestudies/{0}/wmsresources/'
    };

    return config;
}
);
