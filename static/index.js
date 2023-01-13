// 1. Define variables and constant used in global
// Get border of Lausanne comming from app.py (through the index file)
const fronLaus = JSON.parse(border);
// Variables that receive lat/lon from leaflet sent to flask 
// Declare them as false, so only when 4 variables have values, they are sent to routing algo in app.py
lat_dep= false;
lat_dest = false;
lon_dep = false;
lon_dest = false;
// Click variable to count click on leaflet map. To make sure we have 2 clicks that are start/destination 
var click = 0;
// Variable to receive geojson layer containing path and lausanne border from algo routing (coming from app.py) 
var geojson_path, geojson_bound, border_Laus = false;
// Define icons for start/destination markers with some parameters
const icone_depart = L.icon({
  iconUrl: 'static/img/marker_dep.svg',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34]
});
const icone_dest = L.icon({
  iconUrl: 'static/img/marker_dest.svg', 
    iconUrl: 'static/img/marker_dest.svg', 
  iconUrl: 'static/img/marker_dest.svg', 
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34]
});
// Define two markers for destination and start (set lat,lng otherwise does not work, do not know why)
var marker_dest = L.marker((45, 5), {icon:icone_dest}, {draggable: false})
var marker_dep = L.marker((45, 5), {icon:icone_depart}, {draggable: false})

// Different background layers accessible in leaflet 
// OSM
const OpenStreetMap_CH = L.tileLayer('https://tile.osm.ch/switzerland/{z}/{x}/{y}.png', {
	maxZoom: 20,
	attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
	bounds: [[45, 5], [48, 11]]
});
// OSM for cycling 
const CyclOSM = L.tileLayer('https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png', {
	maxZoom: 20,
	attribution: '<a href="https://github.com/cyclosm/cyclosm-cartocss-style/releases" title="CyclOSM - Open Bicycle render">CyclOSM</a> | Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
});
// Satellite imagery
const esriImagery = L.tileLayer(
  'http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: '&copy; <a href="http://www.esri.com">Esri</a>, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
});
// Put them in an object for leaflet control layer 
const baseLayers = {
  'CyclOSM': CyclOSM,
  'OSM CH': OpenStreetMap_CH,
  'Satellite ESRI': esriImagery
};

// Variables for leaflet map
var map = L.map('map'); // contains leaflet map
var legend = L.control({position: 'topright'}); // contains the legend
var info = L.control({position: 'topleft'}); // tooltip containing info 

// Variables for the geosearching adresse toolbar
// Setting geosearch control button
var OpenStreetMapProvider = window.GeoSearch.OpenStreetMapProvider;
// OSM provider
const OSMprovider = new OpenStreetMapProvider({
  params: {
    'accept-language': 'fr', // render results in French
    countrycodes: 'ch', // limit search results to the Switzerland
  },
});

// Selection of the text in the destination toolbar in html  
// Depart
const form_dep = document.getElementById("geosearch-depart");
var input_dep = form_dep.querySelector('input[type="text"]');
// Destination
const form_dest = document.getElementById("geosearch-destination");
var input_dest = form_dest.querySelector('input[type="text"]');

// Selection 
// Select all checkboxes 
const checkboxes_routing = document.querySelectorAll("input[type=checkbox][name=settings]");

// Default settings for the checkboxes
let enabledSettings = ['pente']; // defines it with default settings
let cost_col = 'TC_DWV'; 

// 2. Define functions about events from interactions
function getPath(response){
  if(response.ok) {
      response.json()
      .then(function(response) {
          // Add path two times for better visibility
          geojson_bound = L.geoJson(response, {
            color: 'black',
            weight: 10
        }).addTo(map)
          // Add path with cycling quality as geojson layer 
          geojson_path = L.geoJson(response, {
            style: style,
            onEachFeature: onEachFeature
        }).addTo(map);
        // Fit the leaflet map to the path
        bounds = geojson_path.getBounds();
        map.fitBounds(bounds);
        // Add the legend to the map
        legend.addTo(map);
        // Add the tooltip info 
        info.addTo(map);
        }); // End then 
  }
  else {
      throw Error('Something went wrong');
  }
};
// Deal with invert latlng button 
function invertLatLng() {
  // Make sure that start and destination are defined and path is already added
  if (lat_dep && lat_dest && lon_dep && lon_dest && geojson_path) {
  // Remove markers
  map.removeLayer(marker_dep);
  map.removeLayer(marker_dest);
  // Remove the geojson layers for the path 
  map.removeLayer(geojson_path)
  map.removeLayer(geojson_bound)
  // Invert lat/lng
  lat = lat_dep; 
  lon = lon_dep;
  lat_dep = lat_dest;
  lon_dep = lon_dest;
  lat_dest = lat;
  lon_dest = lon;
  // Invert the markers 
  marker_dep.setLatLng([lat_dep, lon_dep]).addTo(map);
  marker_dest.setLatLng([lat_dest, lon_dest]).addTo(map);
  // fetch those data to app.py
  fetch('/', {
    headers : {
        'Content-Type' : 'application/json'
    },
    method : 'POST',
    body : JSON.stringify( {
    "lat_dep": lat_dep,
    "lon_dep" : lon_dep,
    "lon_dest" : lon_dest,
    "lat_dest" : lat_dest, 
    "Settings": enabledSettings
    }) // end stringify
  }) // end fetch
  .then(getPath)
  .catch(function(error) {
    console.log(error);
    })
} else {
    alert("Impossible d'inverser, le point de départ et de destination n'ont pas été encore définis")
  } 
}; // end invert lat/lng button
// Deal with reset btn event
function reset() {
  // Reset all lat/lon values to false and click to 0
  lat_dep= false;
  lat_dest = false;
  lon_dep = false;
  lon_dest = false;
  click = 0;
  // Remove markers
  map.removeLayer(marker_dep);
  map.removeLayer(marker_dest);
  // Remove the geojson layers for the path 
  if (geojson_path) {
    map.removeLayer(geojson_path);
    map.removeLayer(geojson_bound);
  };
  // Reset all forms and checkboxes to default values
  input_dep.disabled = false;
  input_dep.value="" // empty string as value
  input_dest.disabled = false;
  input_dest.value="" 
  document.getElementById("intersections").checked = false;
  document.getElementById("pente").checked = true;
  enabledSettings = ['pente']
  // Reset the map view to begining
  map.setView([46.5196535, 6.6322734], 13);
  map.fitBounds(bounds_Laus); 
}

// Get color function for coloring of path according to Cycling Quality in leaflet 
function getColor_CQ(d) {
  /* Return color according to the class. The color palette comes from colorbrewer
  https://colorbrewer2.org/?type=diverging&scheme=RdYlBu&n=5 */
  return  d > 2 ? '#d73027' :
          d > 1.5 ? '#f46d43' :
          d > 1.2 ? '#fdae61' :
          d > 1 ? '#ffffbf' :
          d > 0.8 ? '#74add1' :
          '#313695';
  }

// Style function to call in L.geojson to color the path with corresponding cycling quality 
function style(feature) {
  /*
  Function called in L.geojson with parameters style:style ; colors the features in gejson according to their value  ;for now the value is fixed with TC_DWV = Cycling quality with taking into account trafic = DWV (mean trafic for monday-friday)
  */
  if (cost_col == 'TC_DWV'){
    return {
        color: getColor_CQ(feature.properties.TC_DWV),
        fillOpacity: 1,
        weight: 5,
        opacity: 1
    };
  } else if (cost_col == 'TC_noGR') {
    return {
      color: getColor_CQ(feature.properties.TC_noGR),
      fillOpacity: 1,
      weight: 5,
      opacity: 1
    };
  } 
}; // end style feature function


function highlightFeature(e) {
  /*
  Interaction with mousover a layer. Here the layer is geojson layer containing lines constituting the path found by the shortest path algo
  */
  var layer = e.target; // select the layer 
  layer.setStyle({
      weight: 5,
  });
  info.update(layer.feature.properties); // updating the info tooltip 
}

function resetHighlight(e) {
  /*
  Reset the info when mouse is not on the features of geojson layer
  */
  geojson_path.resetStyle(e.target);
  info.update();
}

function onEachFeature(feature, layer) {
  /*
  Function to call in L.geojson (onEachFeature: onEachFeature) to deal with the mouse events.
  Mousover returns the highlight function while mouseout calls the reset info function
  */
  layer.on({
      mouseover: highlightFeature,
      mouseout: resetHighlight,
  });
}

// method that we will use to update the control based on feature properties passed
info.update = function (props) {
  /*
  Get information to display in the info tooltip  
  */ 
 if (cost_col === 'TC_DWV'){
  this._div.innerHTML = '<h4> Info sur le trajet </h4>' +  (props ?
      '<b> Nom : ' + props.name + '</b><br /> Qualité cyclable :' + (props.TC_DWV).toFixed(2) + '<br /> Pente : ' + (props.grade*100).toFixed(2) + ' %' + '<br> Trafic :' + (props.DWV_ALLE).toFixed(0) + ' [véh./jour] <br> Aménagement cyclable : ' + props.Am_cycl
      : 'Passer la souris sur le trajet proposé');
  } else if (cost_col='TC_noGR') {
    this._div.innerHTML = '<h4> Info sur le trajet </h4>' +  (props ?
      '<b> Nom : ' + props.name + '</b><br /> Qualité cyclable :' + (props.TC_noGR).toFixed(2) + '<br /> Pente : ' + (props.grade*100).toFixed(2) + ' %' + '<br> Trafic :' + (props.DWV_ALLE).toFixed(0) + ' [véh./jour] <br> Aménagement cyclable : ' + props.Am_cycl
      : 'Passer la souris sur le trajet proposé');
  } 
};
info.onAdd = function (map) {
  /*
  Create a div with a class "info" in the leaflet map that calls update info 
  */ 
    this._div = L.DomUtil.create('div', 'info');
    this.update();
    return this._div;
};

// Functions about gelocalisation
// Event for clicking on button to get localisation
function onLocationFound(e) {
  // Add marker at click button and get lat/lng
  if (button_id==='btnGetLocStart') {
    marker_dep.setLatLng(e.latlng).addTo(map);
    lat_dep = e.latlng.lat;
    lon_dep = e.latlng.lng;

  } else if (button_id==='btnGetLocDest') { // add marker for destination
    marker_dest.setLatLng(e.latlng).addTo(map);
    lat_dest = e.latlng.lat;
    lon_dest = e.latlng.lng;
  } ; // end else
  // If 4 lat/lon exists, then send it to python using fetch
  if (lat_dep && lat_dest && lon_dep && lon_dest) {
    fetch('/', {
      headers : {
          'Content-Type' : 'application/json'
      },
      method : 'POST',
      body : JSON.stringify( {
      "lat_dep": lat_dep,
      "lon_dep" : lon_dep,
      "lon_dest" : lon_dest,
      "lat_dest" : lat_dest, 
      "Settings": enabledSettings
      }) // end stringify
    }) // end fetch
    .then(getPath)
    .catch(function(error) {
      console.log(error);
      })
  } 

}; // end of location found

function onMapClick(e) {
  if (click >= 2) {
    alert("Vous pouvez seulement définir un point de départ et un point de destination. Vous pouvez soit appuyer sur le bouton reset ou déplacer les marqueurs existants")
    return
  };
  click += 1
  if (lat_dep && lon_dep) { // For the destination
    // Add marker to it
    marker_dest.setLatLng(e.latlng).addTo(map);
    // marker_dest = L.marker(e.latlng, {icon:icone_dest}, {draggable: true}).addTo(map);
    // Get lat/lon coordinates
    lat_dest = e.latlng.lat
    lon_dest = e.latlng.lng
  } else { // To determine start
    // Add marker at the coordinates
    marker_dep.setLatLng(e.latlng).addTo(map);
    // marker_dest = L.marker(e.latlng, {icon:icone_depart}, {draggable: true}).addTo(map);
    // Get lat/lng coordinates
    lat_dep = e.latlng.lat;
    lon_dep = e.latlng.lng;
  }; // end else statement  
  // If all lon/lat exist, send them to python
  if (lat_dep && lat_dest && lon_dep && lon_dest) {
  // Add fetch to send it to flask app
  fetch('/', {
  headers : {
      'Content-Type' : 'application/json'
  },
  method : 'POST',
  body : JSON.stringify( {
  "lon_dep" : lon_dep,
  "lat_dep" : lat_dep,
  "lon_dest" : lon_dest,
  "lat_dest" : lat_dest,
  "Settings": enabledSettings
  }) // end stringify
  }) // end fetch
  .then(getPath)
  .catch(function(error) {
    console.log(error);
    })

  }; // Enf of if condition for fetch 
  
}; // end of click function

// 3. Initialize the leaflet map 
// Set the view
map.setView([46.5196535, 6.6322734], 13); 
// Add border of Lausanne
border_Laus = L.geoJson(fronLaus, {
  color: 'black',
  weight: 2,
  fillOpacity: 0
}).addTo(map);
// fit map to the border
bounds_Laus = border_Laus.getBounds();
map.fitBounds(bounds_Laus);
// Put OSM as default background layer
OpenStreetMap_CH.addTo(map)
// Add possibility to change background layer
L.control.layers(baseLayers).addTo(map);
legend_btn = ''
// Add legend about cycling quality class or gradient class
legend.onAdd = function (map) {
    let grade_breaks = [-10, -5, 0, 5, 10]
    let grade_labels = ['-15% - -10%', '-10% - -5%', '-5% - 0%', '0% - 5%', '5% - 10%', '10% - 15%']
    let cq_breaks = [0.5, 0.8, 1, 1.2, 1.5, 2];
    let cq_labels = ['Très bonne', 'Bonne', 'Acceptable', 'Mauvaise', 'Très mauvaise', 'Extrêmement mauvaise'];

    let div = L.DomUtil.create('div', 'info legend');
    // Construct legend either for cycling quality or grade or cycling infrastructure
    // Loop through our density intervals and generate a label with a colored square for each interval
    // Use if else statements do determine which legend is constructed
    if (legend_btn == 'grade') {
      cost_col = 'grade'
      geojson_path.setStyle(style)
      // Add title for the legend 
      div.innerHTML += 'Pente <br>'
      for (var i = 0; i < grade_breaks.length; i++) {
        div.innerHTML +=
            '<i style="background:' + getColor_Grade(grade_breaks[i]+0.01) + '"></i> ' +
            grade_labels[i] + '<br>';
      }; // end for 
    } else if (legend_btn == 'cycling_infra'){
      div.innerHTML += 'Qualité des infrastructures<br>cyclables<br>'
    } else { // by default, it is cycling quality that is used 
      div.innerHTML += 'Qualité cyclable <br>'
      for (var i = 0; i < cq_breaks.length; i++) {
        div.innerHTML +=
            '<i style="background:' + getColor_CQ(cq_breaks[i]+0.01) + '"></i> ' +
            cq_labels[i] + '<br>';
      }; // end for 
    } // end else 
    
    return div;
};


// 4. Interactivity about gelocalisation 

// 4.1 Localisation by click on a button or clicks on map

// Deal with the click on localisation button event 
// For start 
L.DomEvent.on(document.getElementById('btnGetLocStart'), 'click', function(){
  map.locate({setView: true, maxZoom: 14});
  button_id = this.id; // define button_id to know if clicked to determine start or destination
});
// For destination
L.DomEvent.on(document.getElementById('btnGetLocDest'), 'click', function(){
  map.locate();
  button_id = this.id; // define button_id to know if clicked to determine start or destination
});
// Add it to the map
map.on('locationfound', onLocationFound);
// Deal with the click on map
map.on('click', onMapClick);

// 4.3 Geosearching adress toolbars 
// Start search 
form_dep.addEventListener('submit', async (event) => {
  event.preventDefault();
  const results_dep = await OSMprovider.search({ query: input_dep.value });
  // Selecting data from the results. Take the first results for simplicity
  lon_dep = results_dep[0]['x'];// lon
  lat_dep = results_dep[0]['y']; // lat
  adresse = results_dep[0]['label'] // adresse 
  adresse = adresse.replace(', Plateforme 10', '');
  adresse = adresse.replace(", District de Lausanne", "");
  adresse = adresse.replace(", Suisse", "");
  adresse = adresse.replace(", Vaud", "");
  // Changing the text value in the form in html
  input_dep.value = adresse;
  // Put a marker on the adresse
  marker_dep.setLatLng([lat_dep, lon_dep]).addTo(map);
  // Update click value
  click +=1;

  if (lat_dep && lat_dest && lon_dep && lon_dest) {
    // Add fetch to send it to flask app
    fetch('/', {
    headers : {
        'Content-Type' : 'application/json'
    },
    method : 'POST',
    body : JSON.stringify( {
    "lon_dep" : lon_dep,
    "lat_dep" : lat_dep,
    "lon_dest" : lon_dest,
    "lat_dest" : lat_dest, 
    "Settings": enabledSettings
    })
    })
    .then(getPath)
    .catch(function(error) {
      console.log(error);
      })
  
    }; // 
    
}); // End geosearching depart 

// For destination
form_dest.addEventListener('submit', async (event) => {
  event.preventDefault();
  const results_dest = await OSMprovider.search({ query: input_dest.value });
  // Selecting data from the results. Take the first results for simplicity
  lon_dest = results_dest[0]['x']; // take the first result (if many results)
  lat_dest = results_dest[0]['y']; // take the first result (if many results)
  adresse = results_dest[0]['label'] // adresse
  // Removing unecessary details in adress 
  adresse = adresse.replace(', Plateforme 10', '');
  adresse = adresse.replace(", District de Lausanne", "");
  adresse = adresse.replace(", Suisse", "");
  adresse = adresse.replace(", Vaud", "");
  // Adding the found adresse in the form in html
  input_dest.value = adresse
  // Update click value
  click += 1
  // Adding marker 
  marker_dest.setLatLng([lat_dest, lon_dest]).addTo(map);
  // Need to send those variables to python app.py
  if (lat_dep && lat_dest && lon_dep && lon_dest) {
    // Add fetch to send it to flask app
    fetch('/', {
    headers : {
        'Content-Type' : 'application/json'
    },
    method : 'POST',
    body : JSON.stringify( {
    "lon_dep" : lon_dep,
    "lat_dep" : lat_dep,
    "lon_dest" : lon_dest,
    "lat_dest" : lat_dest, 
    "Settings": enabledSettings
    })
    })
    .then(getPath)
    .catch(function(error) {
      console.log(error);
      })
  
    }; // 
});

// 5. Interactivity with the checkboxes
// For the routing 
// Use Array.forEach to add an event listener to each checkbox. If settings change, a new path is calculated with the new settings 
checkboxes_routing.forEach(function(checkbox) {
  checkbox.addEventListener('change', function() {
    enabledSettings = 
      Array.from(checkboxes_routing) // Convert checkboxes to an array to use filter and map.
      .filter(i => i.checked) // Use Array.filter to remove unchecked checkboxes.
      .map(i => i.value) // Use Array.map to extract only the checkbox values from the array of objects.
    console.log(enabledSettings)
    // Remove existing paths
    if (geojson_path) {
      map.removeLayer(geojson_path)
      map.removeLayer(geojson_bound)
    if (enabledSettings.includes('pente')){
      cost_col = 'TC_DWV'
    // Add fetch to send it to flask app
    fetch('/', {
      headers : {
          'Content-Type' : 'application/json'
      },
      method : 'POST',
      body : JSON.stringify( {
      "lon_dep" : lon_dep,
      "lat_dep" : lat_dep,
      "lon_dest" : lon_dest,
      "lat_dest" : lat_dest, 
      "Settings": enabledSettings
      })
      })
      .then(getPath)
      .catch(function(error) {
        console.log(error);
        })

    } else {
      cost_col = 'TC_noGR'
          // Add fetch to send it to flask app
    fetch('/', {
      headers : {
          'Content-Type' : 'application/json'
      },
      method : 'POST',
      body : JSON.stringify( {
      "lon_dep" : lon_dep,
      "lat_dep" : lat_dep,
      "lon_dest" : lon_dest,
      "lat_dest" : lat_dest, 
      "Settings": enabledSettings
      })
      })
      .then(getPath)
      .catch(function(error) {
        console.log(error);
        })
    } ; // end else
  } // end if geojson_path exist
  }) // End AddEventListener 
});