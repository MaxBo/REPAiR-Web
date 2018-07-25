define([
    'openlayers', 'ol-contextmenu', 'openlayers/css/ol.css', 
    'ol-contextmenu/dist/ol-contextmenu.min.css',
    'static/css/map.css'
], function(ol, ContextMenu)
{
    /**
    *
    * OpenLayers Map with draggable markers, optional context-menu and fullscreen controls
    * @author Christoph Franke
    */
    class Map {

        /**
        * create the map and show it inside the HTMLElement with the given id
        *
        * @param {Object} options
        * @param {string} options.el                           the HTMLElement to render the map into
        * @param {boolean} [options.renderOSM=true]            render default background map
        * @param {string} [options.projection='EPSG:3857']     projection of the map
        * @param {Array.<number>} [options.center=[13.4, 52.5]]  the map will be centered on this point (x, y), defaults to Berlin
        *
        */
        constructor(options){
            var _this = this;
            this.idCounter = 0;
            this.mapProjection = options.projection || 'EPSG:3857';
            this.center = options.center || ol.proj.transform([13.4, 52.5], 'EPSG:4326', this.mapProjection);

            this.view = new ol.View({
                projection: this.mapProjection,
                center: this.center,
                zoom: 10
            });
            this.layers = {};
            var initlayers = [];

            // blank map
            if (options.renderOSM != false){
                initlayers.push(new ol.layer.Tile({
                    source: new ol.source.OSM({crossOrigin: 'anonymous'}),
                    crossOrigin: 'anonymous',
                    tileOptions: {crossOriginKeyword: 'anonymous'},
                }))
            }

            var basicLayer = new ol.layer.Vector({ source: new ol.source.Vector() });
            initlayers.push(basicLayer);

            this.layers = { basic: basicLayer }; 

            this.map = new ol.Map({
                layers: initlayers,
                target: options.el,
                controls: ol.control.defaults({
                    attributionOptions: ({
                        collapsible: false
                    })
                }).extend([
                    new ol.control.FullScreen({source: options.el})
                ]),
                view: this.view
            });

            var _this = this;
            this.map.on('pointermove', function (e) {
                if (e.dragging) return;

                var pixel = _this.map.getEventPixel(e.originalEvent);
                var hit = _this.map.hasFeatureAtPixel(pixel);

                _this.map.getTargetElement().style.cursor = hit ? 'pointer' : '';
            });

            this.div = options.el;

            var tooltip = this.div.querySelector('.tooltip');
            if (!tooltip){
                tooltip = document.createElement('div');
                tooltip.classList.add('tooltip');
                this.div.appendChild(tooltip);
            }
            if (tooltip){
                var overlay = new ol.Overlay({
                    element: tooltip,
                    offset: [10, 0],
                    positioning: 'bottom-left'
                });
                this.map.addOverlay(overlay);

                function displayTooltip(evt) {
                    var pixel = evt.pixel;
                    var feature = _this.map.forEachFeatureAtPixel(pixel, function(feature) {
                        return feature;
                    });
                    if (feature && feature.get('tooltip')) {
                        overlay.setPosition(evt.coordinate);
                        tooltip.innerHTML = feature.get('tooltip');
                        tooltip.style.display = '';
                    }
                    else tooltip.style.display = 'none';
                };

                this.map.on('pointermove', displayTooltip);
            }
        }

        /**
        * transforms given coordinates into projection of map
        *
        * @param {Array.<number>} coordinates  (x,y) coordinates to transform
        * @param {string} projection         projection of the coordinate
        *
        * @returns {Array.<number>} (x,y)      coordinates in map projection
        *
        */
        toMapProjection(coordinate, projection) {
            return ol.proj.transform(coordinate, projection, this.mapProjection);
        }

        /**
        * transforms given coordinates in map projection into given projection
        *
        * @param {Array.<number>} coordinates  (x,y) coordinates in map projection to transform
        * @param {string} projection         projection to transform into
        *
        * @returns {Array.<number>} (x,y)      coordinates in given projection
        *
        */
        toProjection(coordinate, projection) {
            return ol.proj.transform(coordinate, this.mapProjection, projection);
        }

        /**
        * add a new vector layer to map
        *
        * @param {string} name  name of the layer
        * @param {Object=} options
        * @param {string} [options.stroke='rgb(100, 150, 250)']     color of outline
        * @param {string} [options.strokeWidth=1]                   width of outline
        * @param {string} [options.fill='rgba(100, 150, 250, 0.1)'] color of filling
        * @param {string} [options.labelColor='#4253f4']            color of label
        * @param {string=} options.zIndex                           z-index of the layer
        * @param {Object=} options.source                           source layer
        * @param {string=} options.source.projection                projection of the source
        * @param {Object=} options.select                           options for selectable features inside this layer
        * @param {Boolean=} [options.select.selectable=false]       enables selection of features on click
        * @param {string} [options.select.stroke='rgb(230, 230, 0)'] color of outline of selected feature
        * @param {string} [options.select.strokeWidth=3]            width of outline of selected feature
        * @param {string} [options.select.fill='rgba(230, 230, 0, 0.1)'] color of filling of selected feature
        * @param {string} [options.select.labelColor='#e69d00']     color of label selected feature
        * @param {Object} options.select.onChange                   callback 
        *
        * @returns {ol.layer.Vector}                                the added vector layer
        */
        addLayer(name, options){
            
            if (this.layers[name] != null) this.removeLayer(name)
            
            var options = options || {},
                sourceopt = options.source || {},
                source,
                _this = this;
            if (sourceopt.url){
                var source = new ol.source.Vector({
                    format: new ol.format.GeoJSON(),
                    url: sourceopt.url,
                    projection : sourceopt.projection || this.mapProjection,
                })
            }

            var image = new ol.style.Circle({
                radius: 5,
                fill: new ol.style.Fill({ color: options.stroke || 'rgb(100, 150, 250)' }),
                stroke: new ol.style.Stroke({
                    color: options.fill || 'rgba(100, 150, 250, 0.1)', 
                    width: options.strokeWidth || 3
                })
            });

            function labelStyle(feature, resolution) {
                return new ol.style.Text({
                    font: '15px Open Sans,sans-serif',
                    fill: new ol.style.Fill({ color: options.labelColor || '#4253f4' }),
                    stroke: new ol.style.Stroke({
                        color: 'white', width: 3
                    }),
                    text: feature.get('label'),
                    overflow: false
                })
            }
            
            var layer = new ol.layer.Vector({ 
                source: source || new ol.source.Vector(),
                style: (options.colorRange != null) ? colorRangeStyle: defaultStyle
            });
            
            this.layers[name] = layer;
            this.map.addLayer(layer);
            if (options.zIndex) layer.setZIndex(options.zIndex);
            
            var select = options.select || {};

            if (select.selectable){
                function selectLabelStyle(feature, resolution) {
                    return new ol.style.Text({
                        font: '15px Open Sans,sans-serif',
                        fill: new ol.style.Fill({ color: select.labelColor || '#e69d00' }),
                        stroke: new ol.style.Stroke({
                            color: 'white', width: 3
                        }),
                        text: feature.get('label'),
                    })
                }
                layer.selectStyle = function(feature, resolution){ 
                    return new ol.style.Style({
                        image: new ol.style.Circle({
                            radius: 5,
                            fill: new ol.style.Fill({ color: select.stroke || 'rgb(230, 230, 0)' }),
                            stroke: new ol.style.Stroke({
                                color: select.fill || 'rgba(100, 150, 250, 0.1)', 
                                width: select.strokeWidth || 3
                            })
                        }),
                        stroke: new ol.style.Stroke({
                            color: select.stroke || 'rgb(230, 230, 0)',
                            width: select.strokeWidth || 3
                        }),
                        fill: new ol.style.Fill({
                            color: select.fill || 'rgba(230, 230, 0, 0.1)'
                        }),
                        text: selectLabelStyle(feature, resolution)
                    });
                }
                var interaction = new ol.interaction.Select({
                    toggleCondition: ol.events.condition.always,
                    features: layer.selected,
                    layers: [layer],
                    style: layer.selectStyle,
                });
                this.map.addInteraction(interaction);
                layer.select = interaction;
                if (select.onChange){
                    interaction.on('select', function(evt){
                        var selected = evt.selected,
                            deselected = evt.deselected,
                            ret = [];
                        // callback with all currently selected
                        interaction.getFeatures().forEach(function(feat){
                            ret.push({id: feat.get('id'), label: feat.get('label')});
                        })
                        select.onChange(ret);
                        layer.getSource().dispatchEvent('change');
                    })
                }
            }

            function defaultStyle(feature, resolution, strokeColor, fillColor){
                if (feature.selected) return layer.selectStyle(feature, resolution);
                return new ol.style.Style({
                    image: image,
                    stroke: new ol.style.Stroke({
                        color: strokeColor || options.stroke || 'rgb(100, 150, 250)',
                        width: options.strokeWidth || 1
                    }),
                    fill: new ol.style.Fill({
                        color: fillColor || options.fill || 'rgba(100, 150, 250, 0.1)'
                    }),
                    text: labelStyle(feature, resolution)
                });
            }
            
            var alpha = options.alphaFill || 1;
            
            function colorRangeStyle(feature, resolution){
                var value = feature.get('value');
                if (value == null) return defaultStyle(feature, resolution);
                return defaultStyle(feature, resolution, options.colorRange(value).rgba(), options.colorRange(value).alpha(alpha).rgba());
            }
            
            return layer;
        }

        setVisible(layername, visible){
            var layer = this.layers[layername];
            layer.setVisible(visible);
        }

        addServiceLayer(name, options){
            var options = options || {};
            var layer = new ol.layer.Tile({
                opacity: options.opacity || 1,
                visible: (options.visible != null) ? options.visible: true,
                //extent: [-13884991, 2870341, -7455066, 6338219],
                source: new ol.source.TileWMS({
                    url: options.url,
                    params: options.params,
                    serverType: 'geoserver',
                    // Countries have transparency, so do not fade tiles:
                    transition: 0
                })
            })
            if (options.zIndex != null) layer.setZIndex(options.zIndex);
            this.layers[name] = layer;
            this.map.addLayer(layer);
        }

        setZIndex(layername, zIndex){
            this.layers[layername].setZIndex(zIndex);
        }

        /**
        * add a polygon to the map
        *
        * @param {Array.<Array.<number>>} coordinates  coordinates of the polygon
        * @param {Object=} options
        * @param {string} [options.layername='basic']  layer to which the polygon will be added
        * @param {string=} options.projection          projection the given coordinates are in, defaults to map projection
        * @param {string=} options.id                  id of feature
        * @param {string=} options.tooltip             tooltip shown on hover over polygon
        * @param {string=} options.label               label to show on map
        * @param {string} [options.type='Polygon']     Polygon or Multipolygon
        *
        * @returns {ol.geom.Polygon}                   coordinates transformed to a openlayers polygon (same projection as given coordinates were in)
        *
        */
        addPolygon(coordinates, options){
            return this.addGeometry(coordinates, options);
        }
        
        addGeometry(coordinates, options){
            var options = options || {},
                type = options.type || 'Polygon',
                proj = options.projection || this.mapProjection;
            var geometry = (type === 'MultiPolygon') ? new ol.geom.MultiPolygon(coordinates) : 
                           (type === 'Point') ? new ol.geom.Point(coordinates) :
                           (type === 'LineString') ? new ol.geom.LineString(coordinates) :
                           new ol.geom.Polygon(coordinates);
            var ret = geometry.clone();
            var layername = options.layername || 'basic',
                layer = this.layers[layername];

            if (!layer) layer = this.addLayer(layername);
            var feature = new ol.Feature({ geometry: geometry.transform(proj, this.mapProjection) });
            feature.set('label', options.label);
            feature.set('tooltip', options.tooltip);
            feature.set('id', options.id);
            feature.set('value', options.value);
            layer.getSource().addFeature(feature);
            return ret;
        }
        
        getFeatures(layername){
            var layer = this.layers[layername];
            return layer.getSource().getFeatures();
        }
        
        getFeature(layername, id){
            var features = this.getFeatures(layername);
            for (var i = 0; i < features.length; i++){
                var feature = features[i];
                if (feature.get('id') == id) return feature
            }
            return null;
        }
        
        selectFeature(layername, id){
            var feature = this.getFeature(layername, id),
                layer = this.layers[layername];
            layer.select.getFeatures().push(feature);
            layer.select.dispatchEvent({
                type: 'select',
                selected: [feature],
                deselected: []
            });
        }
        /**
        * callback for dragging markers
        *
        * @callback module:visualizations/Map~onDrag
        * @param {Array.<number>} coordinates  (x, y) coordinates in original projection
        */

        /**
        * add a marker to map at given position
        *
        * @param {Array.<number>} coordinates    (x,y) coordinates where marker will be added at
        * @param {Object} options
        * @param {string} [options.layername='basic']  layer to which the marker will be added
        * @param {string=} options.projection  projection the given coordinates are in, uses map projection if not given
        * @param {string=} [options.name='']   the name will be rendered below the marker
        * @param {string=} options.icon        url to image the marker will be rendered with
        * @param {Array.<number>} [options.anchor=[0.5, 0.5]] anchor of icon, defaults to icon center
        * @param {string=} options.dragIcon    url to image the marker will be rendered with while dragging
        * @param {module:visualizations/Map~onDrag=} options.onDrag      callback that will be called when the marker is dragged to new position
        *
        */
        addmarker(coordinates, options) {
            var _this = this;
            var options = options || {};
            var proj = options.projection || this.mapProjection;
            var layername = options.layername || 'basic',
                layer = this.layers[layername];

            var template = '({x}, {y})';

            var feature = new ol.Feature({
                type: 'removable',
                // transform to map projection
                geometry: new ol.geom.Point(
                    this.toMapProjection(coordinates, proj))
            });
            if (options.icon){
                var iconStyle = new ol.style.Style({
                    image: new ol.style.Icon({ scale: .08, src: options.icon, anchor: options.anchor }),
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
                var transformed = ol.proj.transform(coordinate, _this.mapProjection, proj);
                //iconStyle.getText().setText(ol.coordinate.format(transformed, template, 2));
                layer.changed();
                if(options.onDrag){
                    options.onDrag(transformed);
                }
            }, feature);

            this.map.addInteraction(dragInteraction);
            var id = this.idCounter;
            feature.setId(id);
            // remember the interactions to access them on remove by setting them as attributes
            feature.onRemove = options.onRemove;
            feature.removable = options.removable;
            feature.interaction = dragInteraction;
            this.idCounter++;
            layer.getSource().addFeature(feature);
            return id;
        }

        /**
        * move marker with given id to given coordinates
        *
        * @param {Array.<number>} markerId       id of the marker
        * @param {Array.<number>} coordinates    (x,y) coordinates where marker will be added atwhere marker will be added at
        * @param {Object} options
        * @param {string} [options.layername='basic']  the layer the marker is in
        * @param {string=} options.projection          projection the given coordinates are in, uses map projection if not given
        *
        */
        moveMarker(markerId, coordinates, options) {
            var options = options || {};
            var layername = options.layername || 'basic',
                layer = this.layers[layername];
            var feature = layer.getSource().getFeatureById(markerId);
            var proj = options.projection || this.mapProjection;
            feature.setGeometry(new ol.geom.Point(this.toMapProjection(coordinates, proj)));
        }

        /**
        * remove all features from a layer
        *
        * @param {string} layername               the name of the layer
        * @param {Object} options
        * @param {Array.<string>=} options.types  types of the features to remove, defaults to all
        */
        clearLayer(layername, options){
            var options = options || {};
            var layer = this.layers[layername];
            if (options.types == null){
                layer.getSource().clear();
            }
            else {
                var source = layer.getSource();
                // iterate features of the layer and remove those that are in given types
                source.getFeatures().forEach(function(feature){
                    if (options.types.includes(feature.getGeometry().getType()))
                        source.removeFeature(feature);
                })
            }
            if (layer.select) layer.select.getFeatures().clear();
        }

        /**
        * remove layer
        *
        * @param {string} layername   the name of the layer to remove
        */
        removeLayer(layername){
            var layer = this.layers[layername];
            this.map.removeLayer(layer)
            delete this.layers[layername];
        }

        /**
        * remove all interactions from the map
        *
        */
        removeInteractions(){
            var _this = this;
            this.map.getInteractions().forEach(function (interaction) {
                if (interaction instanceof ol.interaction.Modify)
                    _this.map.removeInteraction(interaction);
            });
        }

        // get the layers the given feature is in
        getAssociatedLayers(feature){
            var associated = [];
            var _this = this;
            Object.keys(this.layers).forEach(function(layername){
                var layer = _this.layers[layername];
                if (layer.getSource().getFeatureById(feature.getId()) != null)
                    associated.push(layer);
            })
            return associated;
        }

        // event to remove marker
        removeFeatureEvent(obj) {
            var feature = obj.data.feature;
            if (feature.interaction != null) this.map.removeInteraction(feature.interaction);
            if (feature.onRemove != null) feature.onRemove();

            this.layers = this.getAssociatedLayers(feature);
            this.layers.forEach(function(layer){ layer.getSource().removeFeature(feature); })
        }

        /**
        * callback for clicking item in context menu
        *
        * @callback Map~itemClicked
        * @param {Object} event event
        * @param {Array.<number>} event.coordinate coordinates in map projection
        * @see https://github.com/jonataswalker/ol-contextmenu
        */

        /**
        * add a context menu to the map
        * option to remove marker and zoom controls are always added
        *
        * @param {Array.<{text: string, icon: string, callback: Map~itemClicked}>} contextmenuItems  items to be added to the context menu
        * @see https://github.com/jonataswalker/ol-contextmenu
        */
        addContextMenu(contextmenuItems){
            if (this.contextmenu != null)
                this.map.removeControl(this.contextmenu);
            var contextmenu = new ContextMenu({
                width: 180,
                items: contextmenuItems
            });
            this.contextmenu = contextmenu;
            this.map.addControl(contextmenu);

            var removeFeatureItem = {
                text: 'Remove',
                classname: 'feature',
                callback: this.removeFeatureEvent
            };

            var _this = this;
            contextmenu.on('open', function (evt) {
                var feature = _this.map.forEachFeatureAtPixel(evt.pixel, ft => ft);

                if (feature && feature.get('type') === 'removable' && feature.removable) {
                    contextmenu.clear();
                    removeFeatureItem.data = { feature: feature };
                    contextmenu.push(removeFeatureItem);
                } else {
                    contextmenu.clear();
                    contextmenu.extend(contextmenuItems);
                    contextmenu.extend(contextmenu.getDefaultItems());
                }
            });
        }

        /**
        * center map on given coordinates
        *
        * @param {Array.<number>} coordinates     (x,y) coordinates
        * @param {Object} options
        * @param {string=} options.projection      projection of the coordinates and extent, defaults to map projection
        * @param {Array.<number>=} options.extent  an array of numbers representing an extent: [minx, miny, maxx, maxy], map will be zoomed to fit the extent
        * @param {number=} options.zoomOffset      offset for zooming on extent (negative values will zoom out more)
        */
        centerOnPoint(coordinate, options) {
            var options = options || {};
            var zoom;
            if (options.projection)
                coordinate = this.toMapProjection(coordinate, options.projection)
            if (options.extent){
                var extent = options.extent;
                if (options.projection){
                    var min = this.toMapProjection(extent.slice(0, 2), options.projection);
                    var max = this.toMapProjection(extent.slice(2, 4), options.projection);
                    extent = min.concat(max);
                }
                var resolution = this.view.getResolutionForExtent(extent);
                zoom = this.view.getZoomForResolution(resolution);
                var zoomOffset = options.zoomOffset || 0;
                zoom += zoomOffset;
            }
            this.view.animate({ center: coordinate, zoom: zoom });//, {zoom: 10});
        }

        /**
        * center map on polygon
        *
        * @param {ol.geom.Polygon} polygon      the OpenLayers polygon
        * @param {Object} options
        * @param {string=} options.projection   projection of the coordinates of the polygon
        * @param {number=} options.zoomOffset   offset for zooming on extent (negative values will zoom out more)
        *
        */
        centerOnPolygon(polygon, options) {
            var options = options || {};
            var type = polygon.getType();
            var interior = (type == 'MultiPolygon') ? polygon.getInteriorPoints().getCoordinates()[0]: polygon.getInteriorPoint().getCoordinates();
            var centroid = interior.slice(0, 2);
            var extent = polygon.getExtent();
            options.extent = extent;
            this.centerOnPoint(centroid, options);
            return centroid;
        }
        
        centerOnCoordinates(coordinates, options){
            var poly = new ol.geom.Polygon(coordinates);
            this.centerOnPolygon(poly, options);
        }

        /**
        * centers map on layer with given name, zooms to fit extent of layer
        *
        * @param {string} layername  layer to center on
        *
        */
        centerOnLayer(layername){
            var layer = this.layers[layername],
                source = layer.getSource();

            this.map.getView().fit(source.getExtent(), this.map.getSize());
        }

        /**
        * toggle drawing tool, only one is active at a time, disable drawing
        * by passing type 'None' (or nothing at all)
        *
        * @param {string} layername          layer to draw on
        * @param {Object} options
        * @param {string} [options.type='None']      type of geometry to draw ('Polygon', 'Point', 'Circle', 'LineString', 'None')
        * @param {Boolean} [options.freehand=false]  freehand drawing or drawing by setting points
        *
        */
        toggleDrawing(layername, options){
            var layer = this.layers[layername],
                options = options || {},
                type = options.type || 'None',
                freehand = options.freehand;
                
            if (layer.drawingInteraction)
                this.map.removeInteraction(layer.drawingInteraction);
            layer.drawingInteraction = null;
            if (type === 'None') return;
            
            var source = layer.getSource(),
                draw = new ol.interaction.Draw({
                    source: source,
                    type: type,
                    freehand: options.freehand
                });
            layer.drawingInteraction = draw;
            this.map.addInteraction(draw);
            }
            
        /**
        * enable/disable drag box to select features
        * (only works when layer supports selection, see addLayer)
        *
        * @param {string} layername   layer whose features to select
        * @param {Boolean} [enabled=true]    enable if true (or null), disable if false
        *
        */
        enableDragBox(layername, enabled){
            var layer = this.layers[layername];
            if (!layer.select) return;
            if (enabled === null || enabled === true){
                // it's already there
                if (layer.dragBox) return;
                layer.dragBox = new ol.interaction.DragBox();
                this.map.addInteraction(layer.dragBox);
                layer.dragBox.on('boxend', function() {
                    var extent = layer.dragBox.getGeometry().getExtent();
                    layer.select.getFeatures().clear();
                    layer.getSource().forEachFeatureIntersectingExtent(extent, function(feature) {
                        layer.select.getFeatures().push(feature);
                        layer.select.dispatchEvent({
                            type: 'select',
                            selected: [feature],
                            deselected: []
                        });
                    });
                });
            }
            else if (layer.dragBox){
                this.map.removeInteraction(layer.dragBox);
                layer.dragBox = null;
            }
        }
        
        /**
        * enable/disable selection of features, requires initialization of layer 
        * with select options (see addLayer)
        *
        * @param {string} layername          layer to enable selection of features in
        * @param {Boolean} [enable=true]     set to false to disable selection
        *
        */
        enableSelect(layername, enable){
            var layer = this.layers[layername];
            if (!layer.select) return;
            if (enable === false) this.map.removeInteraction(layer.select);
            else this.map.addInteraction(layer.select);
        }
        
        /**
        * remove the selected features from layer
        *
        * @param {string} layername  layer to remove features from
        */
        removeSelectedFeatures(layername){
            var layer = this.layers[layername],
                source = layer.getSource();
            if (!layer.select) return;
            layer.select.getFeatures().forEach(function(feat){
                source.removeFeature(feat);
            })
            layer.select.getFeatures().clear();
        }
        
        /**
        * get the feature inside layer with given name
        *
        * @param {string} layername  layer to retrieve features from
        *
        */
        getFeatures(layername){
            var layer = this.layers[layername],
                source = layer.getSource();
            return source.getFeatures();
        }

        /**
        * remove map
        */
        close(){
            this.map.setTarget(null);
            this.map = null;
            this.div.innerHTML = '';
        }

    };


    return Map;
});
