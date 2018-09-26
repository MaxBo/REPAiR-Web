require(['d3', 'underscore', 'models/casestudy', 'collections/geolocations',
         'openlayers', 'app-config', 'openlayers/css/ol.css', 'base'
], function (d3, _, CaseStudy, GeoLocations, ol, config) {

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
            center: ol.proj.fromLonLat([9, 46]),
            zoom: 5
        })
    });

    var imgWidth = 0;

    function renderCaseStudies(caseStudies){
        var features = [];

        caseStudies.forEach(function(caseStudy){
            var properties = caseStudy.get('properties'),
                focusarea = properties.focusarea;
            if (!focusarea || !properties.show_on_welcome_map) return;
            var poly = new ol.geom.MultiPolygon(focusarea.coordinates),
                interior = poly.getInteriorPoints(),
                projCentroid = ol.proj.fromLonLat(interior.getCoordinates()[0]);
            // don't render if wrong projection was returned from api, should be 4326
            if (isNaN(projCentroid[0]) || isNaN(projCentroid[1])) return;
            var feature = new ol.Feature({
                geometry: new ol.geom.Point(projCentroid),
                name: properties.name
            });
            feature.set('id', caseStudy.id);
            var iconStyle = new ol.style.Style({
                image: new ol.style.Icon({
                    anchor: [0.5, 0.5],
                    //offsetOrigin: 'top-left',
                    //offset: [imgWidth, 0],
                    anchorXUnits: 'fraction',
                    anchorYUnits: 'fraction',
                    src: '/static/img/repair-logo-wo-inner-text.png'
                }),
                text: new ol.style.Text({
                    text: properties.name,
                    font: '18px sans-serif',
                    textAlign: 'center',
                    textBaseline: 'middle',
                    fill: new ol.style.Fill({
                        color: 'white',
                    }),
                    stroke: new ol.style.Stroke({
                        color: '#444444',
                        width: 3
                    })
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
        // workaround for misplaced bboxes of icons
        map.updateSize();
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

    function alert(e){
        var title = gettext('Error'),
            message = e.responseText,
            el = document.getElementById('alert-modal'),
            html = document.getElementById('alert-modal-template').innerHTML,
            template = _.template(html);
        console.log(e)

        el.innerHTML = template({ title: title, message: message });
        $(el).modal('show');
    }

    // display popup on click
    map.on('click', function(evt) {
        var pixel = evt.pixel;
        pixel[0] -= (imgWidth / 2);
        var feature = map.forEachFeatureAtPixel(evt.pixel,
            function(feature) {
                return feature;
            });
        if (feature) {
            var csId = feature.get('id');
            config.session.switchCaseStudy(csId, {
                success: function(){
                    window.location.href = '/study-area';
                },
                error: function(e){
                    alert(e)
                }
            });
        }
    });

    map.on('pointermove', function(evt) {
        var pixel = evt.pixel;
        pixel[0] -= (imgWidth / 2);
        map.getTargetElement().style.cursor =
            map.hasFeatureAtPixel(evt.pixel) ? 'pointer' : '';
    });


});


