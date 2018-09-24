require(['d3', 'models/casestudy', 'collections/geolocations', 'openlayers',
    'openlayers/css/ol.css', 'base'
], function (d3, CaseStudy, GeoLocations, ol) {

    document.getElementById('wrapper').style.overflow = 'hidden';
    document.getElementById('content').style.padding = '0px';
    document.getElementById('page-content-wrapper').style.padding = '0px';

    var map = new ol.Map({
        layers: [
            //new ol.layer.Tile({
                //source: new ol.source.OSM()
            //}),
            new ol.layer.Tile({
                source: new ol.source.XYZ({
                    url: 'https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png'
                })
            })
        ],
        controls: [],
        interactions: ol.interaction.defaults({
            doubleClickZoom :false,
            dragAndDrop: false,
            keyboardPan: false,
            keyboardZoom: false,
            mouseWheelZoom: false,
            pointer: false,
            select: false
        }),
        target: 'welcome-map',
        view: new ol.View({
            center: ol.proj.fromLonLat([9, 45]),
            zoom: 5
        })
    });

    function renderCaseStudies(caseStudies){
        var features = [];

        caseStudies.forEach(function(caseStudy){
            var properties = caseStudy.get('properties'),
                centroid = properties.point_on_surface;
            if (!centroid) return;
            var projCentroid = ol.proj.fromLonLat(centroid.coordinates);
            // wrong projection returned from api, should be 4326
            if (isNaN(projCentroid[0]) || isNaN(projCentroid[1])) return;
            var feature = new ol.Feature({
                geometry: new ol.geom.Point(projCentroid),
                name: properties.name
            });
            var iconStyle = new ol.style.Style({
                image: new ol.style.Icon({
                    anchor: [0.5, 0.5],
                    //offsetOrigin: 'top-left',
                    //offset: [35, 0],
                    anchorXUnits: 'fraction',
                    anchorYUnits: 'fraction',
                    src: '/static/img/repair-logo-wo-text.png'
                })
            });
            feature.setStyle(iconStyle);
            features.push(feature);
        })

        var vectorSource = new ol.source.Vector({
            features: features
        });
        var vectorLayer = new ol.layer.Vector({
            source: vectorSource
        });
        map.addLayer(vectorLayer);
    }

    var caseStudies = new GeoLocations([], {
        model: CaseStudy,
        apiTag: 'casestudies'
    });

    caseStudies.fetch({
        data: { all: true },
        success: function(){
            renderCaseStudies(caseStudies)
        }
    })

    var element = document.getElementById('popup');
    var popup = new ol.Overlay({
        element: element,
        positioning: 'bottom-center',
        stopEvent: false,
        offset: [35, -50]
    });
    map.addOverlay(popup);

    // display popup on click
    map.on('click', function(evt) {
        var pixel = evt.pixel;
        pixel[0] -= 35;
        var feature = map.forEachFeatureAtPixel(evt.pixel,
            function(feature) {
                return feature;
            });
        if (feature) {
            var coordinates = feature.getGeometry().getCoordinates();
            $(element).popover({
                placement: 'top',
                html: true
            });
            var popover = $(element).data('bs.popover')
            popover.options.content = feature.get('name');
            popup.setPosition(coordinates);
            $(element).popover('show');
        } else {
            $(element).popover('destroy');
        }
    });

    map.on('pointermove', function(evt) {
        var pixel = evt.pixel;
        pixel[0] -= 35;
        map.getTargetElement().style.cursor =
            map.hasFeatureAtPixel(evt.pixel) ? 'pointer' : '';
    });


});


