define([
  'openlayers', 'ol-contextmenu'
], function(ol, ContextMenu)
{

  var view = new ol.View({
    projection: 'EPSG:3857',
    center: ol.proj.transform([13.4, 52.5], 'EPSG:4326', 'EPSG:3857'),
    zoom: 10
  });
  var vectorLayer = new ol.layer.Vector({ source: new ol.source.Vector() });
  
  var Map = function(options){
    var map = new ol.Map({
      layers: [
        new ol.layer.Tile({
          source: new ol.source.OSM({crossOrigin: 'anonymous'}),
        }),
        vectorLayer
      ],
      target: options.divid,
      controls: ol.control.defaults({
        attributionOptions: /** @type {olx.control.AttributionOptions} */ ({
          collapsible: false
        })
      }).extend([
        new ol.control.FullScreen({source: options.divid})
      ]),
      view: view
    });
    
  var pin_icon_blue = '/static/img/simpleicon-places/svg/map-marker-blue.svg';
  var pin_icon_red = '/static/img/simpleicon-places/svg/map-marker-red.svg';
  this.addmarker = function(obj, options) {
    var coord4326 = ol.proj.transform(obj.coordinate, 'EPSG:3857', 'EPSG:4326'),
        template = '({x}, {y})',
        feature = new ol.Feature({
          type: 'removable',
          geometry: new ol.geom.Point(obj.coordinate)
        });

    if (options.icon){
       var iconStyle = new ol.style.Style({
        image: new ol.style.Icon({ scale: .08, src: options.icon }),
        text: new ol.style.Text({
          offsetY: 25,
          text: ol.coordinate.format(coord4326, template, 2),
          font: '15px Open Sans,sans-serif',
          fill: new ol.style.Fill({ color: '#111' }),
          stroke: new ol.style.Stroke({ color: '#eee', width: 2 })
        })
      });
      feature.setStyle(iconStyle);
    }
    vectorLayer.getSource().addFeature(feature);
    }
  
    var _this = this;
    var contextmenu_items = [
      {
        text: 'Add/Move Administr. Loc.',
        icon: pin_icon_blue,
        callback: function(obj){ _this.addmarker(obj, { icon: pin_icon_blue })}
      },
      {
        text: 'Add Operational Loc.',
        icon: pin_icon_red,
        callback: function(obj){ _this.addmarker(obj, { icon: pin_icon_red })}
      },
      '-' // this is a separator
    ];
    
    var contextmenu = new ContextMenu({
      width: 180,
      items: contextmenu_items
    });
    map.addControl(contextmenu);
    
    var removeMarkerItem = {
      text: 'Remove this Marker',
      classname: 'marker',
      callback: removeMarker
    };
    
    contextmenu.on('open', function (evt) {
      var feature = map.forEachFeatureAtPixel(evt.pixel, ft => ft);
      
      if (feature && feature.get('type') === 'removable') {
        contextmenu.clear();
        removeMarkerItem.data = { marker: feature };
        contextmenu.push(removeMarkerItem);
      } else {
        contextmenu.clear();
        contextmenu.extend(contextmenu_items);
        contextmenu.extend(contextmenu.getDefaultItems());
      }
    });
    
    map.on('pointermove', function (e) {
      if (e.dragging) return;
    
      var pixel = map.getEventPixel(e.originalEvent);
      var hit = map.hasFeatureAtPixel(pixel);
    
      map.getTargetElement().style.cursor = hit ? 'pointer' : '';
    });
    
    // from https://github.com/DmitryBaranovskiy/raphael
    function elastic(t) {
      return Math.pow(2, -10 * t) * Math.sin((t - 0.075) * (2 * Math.PI) / 0.3) + 1;
    }
    
    function center(obj) {
      view.animate({
        duration: 700,
        easing: elastic,
        center: obj.coordinate
      });
    }
    
    function removeMarker(obj) {
      vectorLayer.getSource().removeFeature(obj.data.marker);
    }

  };
  
  
  return Map
});