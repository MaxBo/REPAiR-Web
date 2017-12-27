define([
  'openlayers', 'ol-contextmenu'
], function(ol, ContextMenu)
{
  var Map = function(options){
    var idCounter = 0;
    var interactions = [];
    var map_projection = 'EPSG:3857';

    var view = new ol.View({
      projection: map_projection,
      center: ol.proj.transform([13.4, 52.5], 'EPSG:4326', map_projection),
      zoom: 10
    });
    var vectorLayer = new ol.layer.Vector({ source: new ol.source.Vector() });
  
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
    
    this.toMapProjection = function(coordinate, projection) {
      return ol.proj.transform(coordinate, projection, map_projection);
    }
    
    this.toProjection = function(coordinate, projection) {
      return ol.proj.transform(coordinate, map_projection, projection);
    }
    
    this.addmarker = function(coordinates, options) {
      var proj = options.projection || map_projection;
      
      var template = '({x}, {y})';
          
      var feature = new ol.Feature({
            type: 'removable',
            // transform to map projection
            geometry: new ol.geom.Point(
              this.toMapProjection(coordinates, proj))
          });
      if (options.icon){
         var iconStyle = new ol.style.Style({
          image: new ol.style.Icon({ scale: .08, src: options.icon }),
          text: new ol.style.Text({
            offsetY: 25,
            text: options.name, //ol.coordinate.format(coordinate, template, 2),
            font: '15px Open Sans,sans-serif',
            fill: new ol.style.Fill({ color: '#111' }),
            stroke: new ol.style.Stroke({ color: '#eee', width: 2 })
          })
        });
        feature.setStyle(iconStyle); 
      }
      var dragStyle;
      if (options.dragIcon){
         dragStyle = new ol.style.Style({
          image: new ol.style.Icon({ scale: .08, src: options.dragIcon })
        })
      }
      
      // Drag and drop feature
      var dragInteraction = new ol.interaction.Modify({
          features: new ol.Collection([feature]),
          style: dragStyle,
          pixelTolerance: 20
      });
      
      // Add the event to the drag and drop feature
      dragInteraction.on('modifyend', function(){
        var coordinate = feature.getGeometry().getCoordinates();
        var transformed = ol.proj.transform(coordinate, map_projection, proj);
        //iconStyle.getText().setText(ol.coordinate.format(transformed, template, 2));
        vectorLayer.changed();
        if(options.onDrag){
          options.onDrag(transformed);
        }        
      }, feature);
      
      interactions.push(dragInteraction);
      map.addInteraction(dragInteraction);
      var id = idCounter;
      feature.setId(id);
      idCounter++;
      vectorLayer.getSource().addFeature(feature);
      console.log(feature);
      return id;
    }
    
    this.moveMarker = function(markerId, coordinates, options) {
      var feature = vectorLayer.getSource().getFeatureById(markerId);
      var options = options || {};
      var proj = options.projection || map_projection;
      feature.setGeometry(new ol.geom.Point(this.toMapProjection(coordinates, proj)));
    }
    
    this.removeMarkers = function(){
      map.getInteractions().forEach(function (interaction) {
          if (interaction instanceof ol.interaction.Modify) 
             map.removeInteraction(interaction);
      });
      vectorLayer.getSource().clear();
    };
    
    function removeMarker(obj) {
      vectorLayer.getSource().removeFeature(obj.data.marker);
    }
    
    this.addContextMenu = function (contextmenu_items){
      if (this.contextmenu != null)
        this.map.removeControl(this.contextmenu);
      var contextmenu = new ContextMenu({
        width: 180,
        items: contextmenu_items
      });
      this.contextmenu = contextmenu;
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
    }
    
    map.on('pointermove', function (e) {
      if (e.dragging) return;
    
      var pixel = map.getEventPixel(e.originalEvent);
      var hit = map.hasFeatureAtPixel(pixel);
    
      map.getTargetElement().style.cursor = hit ? 'pointer' : '';
    });
    
    this.center = function(coordinate, options) {
      if (options.projection)
        coordinate = this.toMapProjection(coordinate, options.projection)
      
      view.animate({center: coordinate});//, {zoom: 10});
    }
    
    this.map = map;

  };
  
  
  return Map;
});