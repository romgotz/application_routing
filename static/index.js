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


// 2. Initialize leaflet map and center view on Lausanne
var map = L.map('map').setView([46.5, 6.6], 13);

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
// Define marker variable
var marker 
marker_exist = false

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
  if (marker_exist) {
    map.removeLayer(marker)
  };
  // Add marker at click button and get lat/lng
  if (button_id==='btnGetLocStart') {
    marker_dep = L.marker(e.latlng, {icon:icone_depart}, {draggable: true}).addTo(map);
    marker_dep_exist = true;
    lat_dep = e.latlng.lat;
    lon_dep = e.latlng.lng;
/*  // Add fetch to send it to flask app
    fetch('/', {
    headers : {
        'Content-Type' : 'application/json'
    },
    method : 'POST',
    body : JSON.stringify( {
    "lon_dep" : lon_dep,
    "lat_dep" : lat_dep
    })
    }) // end of fetch for start */
  } else if (button_id==='btnGetLocDest') { // add marker for destination
    marker_dest = L.marker(e.latlng, {icon:icone_dest}, {draggable: true}).addTo(map);
    marker_dest_exist = true;
    lat_dest = e.latlng.lat;
    lon_dest = e.latlng.lng;
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
      "lon_dest" : lon_dest,
      "lat_dest" : lat_dest
    })
    }) // end of fetch for dest
  } else {
    console.log("All lat/lon do not exist yet")
  } // End of if for fetch

}; // end of location found

// Add it to the map
map.on('locationfound', onLocationFound);

// 2nd possiblity : click on the map : it creates a marker
//newMarkerGroup = new L.LayerGroup();
//map.on('click', addMarker);
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
    // Get lat/lon coordinates
    lat_dest = e.latlng.lat;
    lon_dest = e.latlng.lng;
    // Add marker at click button
    marker_dest = L.marker(e.latlng, {icon:icone_dest}, {draggable: true}).addTo(map);
    marker_exist = true;
  } else {
    console.log("This click is to determine the start")
    lat_dep = e.latlng.lat;
    lon_dep = e.latlng.lng;
    // Add marker at the coordinates
    marker_dest = L.marker(e.latlng, {icon:icone_depart}, {draggable: true}).addTo(map);
    marker_exist = true;
  }; // end else statement  
  // If all lon/lat exist, send them to python
  if (lat_dep && lat_dest && lon_dep && lon_dest) {
  console.log("All lat/lon exist, sending them to flask using fetch")
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
            console.log(response);
            console.log("The sending of the data from python file works")
        });
    }
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
  console.log("The lat lon have been defined for the start")
  if (lat_dep && lat_dest && lon_dep && lon_dest) {
    console.log("All lat/lon exist, sending them to flask using fetch")
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
              console.log(response);
              console.log("The sending of the data from python file works")
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
  L.marker([lat_dest,lon_dest], {icon: icone_dest}).addTo(map);
  console.log("The destination adresse has been defined")
  // Need to send those variables to python app.py
  if (lat_dep && lat_dest && lon_dep && lon_dest) {
    console.log("All lat/lon exist, sending them to flask using fetch")
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
              console.log(response);
              console.log("The sending of the data from python file works")
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
