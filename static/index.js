// Define variables that will be used in script
// const proj = L.CRS.EPSG3857;
const proj_4326 = L.CRS.EPSG4326
const proj_3857 = L.CRS.EPSG3857

/* console.log(proj4.defs('EPSG:3857'))
proj4.defs('EPSG:3857');
 */
// 1. Define icons for start/destination markers
var icone_depart = L.icon({
    iconUrl: 'static/img/marker_dep.svg',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34]
});
var icone_dest = L.icon({
    iconUrl: 'static/img/marker_dest.svg', 
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34]
    });

var geojson;

// Determining functions to style trajet according to cycling quality
// Get color function for cycling quality 
function getColor(d) {
      return d > 1.3 ? '#d7191c' :
             d > 1.1   ? '#fdae61' :
             d > 0.95   ? '#ffffbf' :
             d > 0.75   ? '#abd9e9' :
                        '#2c7bb6';
  }
// https://colorbrewer2.org/?type=diverging&scheme=RdYlBu&n=5

function style(feature) {
  return {
      color: getColor(feature.properties.TC_DWV),
      fillOpacity: 0.9
  };
}
// Interaction with polyline : when mousover tooltip 
function highlightFeature(e) {
  var layer = e.target;
  layer.setStyle({
      weight: 5,
  });
  info.update(layer.feature.properties);

}

function resetHighlight(e) {
  geojson.resetStyle(e.target);
  info.update();
}

function onEachFeature(feature, layer) {
  layer.on({
      mouseover: highlightFeature,
      mouseout: resetHighlight,
  });
}

var info = L.control();

info.onAdd = function (map) {
    this._div = L.DomUtil.create('div', 'info'); // create a div with a class "info"
    this.update();
    return this._div;
};

// method that we will use to update the control based on feature properties passed
info.update = function (props) {
    this._div.innerHTML = '<h4> Informations </h4>' +  (props ?
        '<b>' + props.name + '</b><br />' + props.TC_DWV + ' Qualité cyclable '
        : 'Hover sur le trajet proposé');
};


// 2. Initialize leaflet map and center view on Lausanne 
var map = L.map('map').setView([46.5196535, 6.6322734], 13); 
info.addTo(map);

// 2.1 Add different layers 
// OSM
var OpenStreetMap_CH = L.tileLayer('https://tile.osm.ch/switzerland/{z}/{x}/{y}.png', {
	maxZoom: 20,
	attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
	bounds: [[45, 5], [48, 11]]
});
// OSM for cycling 
var CyclOSM = L.tileLayer('https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png', {
	maxZoom: 20,
	attribution: '<a href="https://github.com/cyclosm/cyclosm-cartocss-style/releases" title="CyclOSM - Open Bicycle render">CyclOSM</a> | Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
});
var esriImagery = L.tileLayer(
  'http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: '&copy; <a href="http://www.esri.com">Esri</a>, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
});

// Put all layers to choose
var baseLayers = {
  'CyclOSM': CyclOSM,
  'OSM CH': OpenStreetMap_CH,
  'Satellite ESRI': esriImagery
};

// Initialize with OSM
OpenStreetMap_CH.addTo(map)
L.control.layers(baseLayers).addTo(map)

// 3. Interactivity about gelocalisation 

// 3.1 Get actual localisation by click on a button
// Declare lat/lon as false, need to have 4 values before data is sent to flask 
lat_dep= false
lat_dest = false
lon_dep = false
lon_dest = false

// Deal with the event, either click on start or destination 
// For start 
L.DomEvent.on(document.getElementById('btnGetLocStart'), 'click', function(){
  map.locate({setView: true, maxZoom: 16});
  button_id = this.id;
});
// For destination
L.DomEvent.on(document.getElementById('btnGetLocDest'), 'click', function(){
  map.locate({setView: true, maxZoom: 16});
  button_id = this.id;
});

// Display marker at localisation 
function onLocationFound(e) {
  // Add marker at click button and get lat/lng
  if (button_id==='btnGetLocStart') {
    marker_dep = L.marker(e.latlng, {icon:icone_depart}, {draggable: true}).addTo(map);
    lat_dep = e.latlnglng.lat;
    lon_dep = e.latlnglng.lng;

  } else if (button_id==='btnGetLocDest') { // add marker for destination
    marker_dest = L.marker(e.latlng, {icon:icone_dest}, {draggable: true}).addTo(map);
    lat_dest = e.latlnglng.lat;
    lon_dest = e.latlnglng.lng;
  } ; // end else
  // If 4 lat/lon exists, then send it to python using fetch
  if (lat_dep && lat_dest && lon_dep && lon_dest) {
    console.log("All lat/lon exist, sending them to flask using fetch")
    fetch('/', {
      headers : {
          'Content-Type' : 'application/json'
      },
      method : 'POST',
      body : JSON.stringify( {
      "lat_dep": lat_dep,
      "lon_dep" : lon_dep,
      "lon_dest" : lon_dest,
      "lat_dest" : lat_dest
    })
    .then(function (response){
      if(response.ok) {
          response.json()
          .then(function(response) {
              console.log("The sending of the data from python file works");
            });
      }
      else {
          throw Error('Something went wrong');
      }
      })
    .catch(function(error) {
      console.log(error);
      })
    }) // end of fetch for dest
  } else {
    console.log("All lat/lon do not exist yet")
  } // End of if for fetch

}; // end of location found

// Add it to the map
map.on('locationfound', onLocationFound);

// 2nd possiblity : click on the map : it creates a marker

// Have to add difference btw 1st click = depart and 2nd click = destination

var click = 0

function onMapClick(e) {
  if (click >= 2) {
    alert("Vous pouvez seulement définir un point de départ et un point de destination. Vous pouvez soit appuyer sur le bouton reset ou déplacer les marqueurs existants")
    return
  };
  click += 1
  if (lat_dep && lon_dep) {
    console.log("This click is to determine the destination.")
    // Add marker to it
    marker_dest = L.marker(e.latlng, {icon:icone_dest}, {draggable: true}).addTo(map);
    // Get lat/lon coordinates
    lat_dest = e.latlng.lat
    lon_dest = e.latlng.lng
  } else {
    console.log("This click is to determine the start")
    // Add marker at the coordinates
    marker_dest = L.marker(e.latlng, {icon:icone_depart}, {draggable: true}).addTo(map);
    // Get lat/lng and project them in epsg 3857
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
  "lat_dest" : lat_dest
  })
  })
  .then(function (response){
    if(response.ok) {
        response.json()
        .then(function(response) {
          console.log("The sending of the data from python file works")
          console.log(response)
          console.log(response.features[0].properties.TC_DWV)
          // data = TC_DWV
          geojson = L.geoJson(response, {
            style: style,
            onEachFeature: onEachFeature
        }).addTo(map)
        }) // End of then 
      } // end if

    else {
        throw Error('Something went wrong');
    }
    })
  .catch(function(error) {
    console.log(error);
    })

  }; // Enf of if condition for fetch 
  
}; // end of click function

// Deal with the event on map
map.on('click', onMapClick);

// 4.3 Geosearching adresse

// Setting geosearch control button
var OpenStreetMapProvider = window.GeoSearch.OpenStreetMapProvider;
// var GeoSearchControl = window.GeoSearch.GeoSearchControl;

// Define parameters for geosearching
const OSMprovider = new OpenStreetMapProvider({
  params: {
    'accept-language': 'fr', // render results in French
    countrycodes: 'ch', // limit search results to the Switzerland
    autoClose: true,
    autoComplete: true
  },
});

/* const searchControl = new GeoSearchControl({
  provider: new OpenStreetMapProvider(),
  style: 'bar',
  //--------
  // if autoComplete is false, need manually calling provider.search({ query: input.value })
  autoComplete: true,         // optional: true|false  - default true
  autoCompleteDelay: 250
}) */

// For start
const form_depart = document.getElementById('geosearch_depart')
const input_dep = form_depart.querySelector('input[type="text"]');

form_depart.addEventListener('submit', async (event) => {
  if (lat_dep && lon_dep) {
    alert("Vous avez déjà déterminé le point de départ. Voulez-vous définir un nouveau point de départ ?")
    return 
  };
  event.preventDefault();
  const results_dep = await OSMprovider.search({ query: input_dep.value });
  lon_dep = results_dep[0]['x'];// take the first result (if many results)
  lat_dep = results_dep[0]['y']; // take the first result (if many results)
  // Put a marker on the adresse
  L.marker([lat_dep,lon_dep], {icon: icone_depart}).addTo(map);

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
    "lat_dest" : lat_dest
    })
    })
    .then(function (response){
      if(response.ok) {
          response.json()
          .then(function(response) {
              console.log("The sending of the data from python file works")
              var myLayer = L.geoJson(response).addTo(map);
          });
      }
      else {
          throw Error('Something went wrong');
      }
      })
    .catch(function(error) {
      console.log(error);
      })
  
    }; // 
    
}); // End geosearching depart

// For destination
// Geosearching for destination
const form_dest = document.getElementById('geosearch_dest');
const input_dest = form_dest.querySelector('input[type="text"]');

form_dest.addEventListener('submit', async (event) => {
  if (lat_dest && lon_dest) {
    alert("Vous avez déjà déterminé la destination. Voulez-vous définir une nouvelle destination ?")
    return 
  };
  event.preventDefault();
  const results_dest = await OSMprovider.search({ query: input_dest.value });
  lon_dest = results_dest[0]['x']; // take the first result (if many results)
  lat_dest = results_dest[0]['y']; // take the first result (if many results)
  // Add marker to the map
  L.marker([lat_dest,lon_dest], {icon: icone_dest}).addTo(map);
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
    "lat_dest" : lat_dest
    })
    })
    .then(function (response){
      if(response.ok) {
          response.json()
          .then(function(response) {
              console.log("The sending of the data from python file works")
              var myLayer = L.geoJson(response).addTo(map)
          });
      }
      else {
          throw Error('Something went wrong');
      }
      })
    .catch(function(error) {
      console.log(error);
      })
  
    }; // 
});

