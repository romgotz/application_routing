/* 


map.addControl(searchControl); */

// 2. Define icons for start/destination markers
const icone_depart = L.icon({
    iconUrl: 'static/img/marker_dep.svg',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34]
});
const icone_dest = L.icon({
    iconUrl: 'static/img/marker_dest.svg', 
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34]
    });


// 3. Initialize leaflet map and center view on Lausanne
var map = L.map('map').setView([46.5, 6.6], 13);

// 3.1 Add different layers 
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

// 4. Interactivity about gelocalisation 

// 4.1 Get actual localisation by click on a button
// Deal with the event 
L.DomEvent.on(document.getElementById('btnGetLoc'), 'click', function(){
  map.locate({setView: true, maxZoom: 16});
})

// Display marker at localisation 
function onLocationFound(e) {
  L.marker(e.latlng, {icon:icone_depart}).addTo(map)

};

// Add it to the map
map.on('locationfound', onLocationFound);

// 2nd possiblity : click on the map : it creates a marker
//newMarkerGroup = new L.LayerGroup();
//map.on('click', addMarker);
// Have to add difference btw 1st click = depart and 2nd click = destination

var marker = L.marker({icon:icone_depart})

function onMapClick(e) {
  // L.marker(e.latlng, {icon: icone_depart}).addTo(map)
  marker
      .setIcon(icone_depart)
      .setLatLng(e.latlng)
      .addTo(map)
}

map.on('click', onMapClick);


// 4.3 Geosearching adresse

// Setting geosearch control button
// var GeoSearchControl = window.GeoSearch.GeoSearchControl;
var OpenStreetMapProvider = window.GeoSearch.OpenStreetMapProvider;

// Define parameters for geosearching
const OSMprovider = new OpenStreetMapProvider({
  params: {
    'accept-language': 'fr', // render results in French
    countrycodes: 'ch', // limit search results to the Switzerland
    autoClose: true,
    autoComplete: true
  },
});

// For start
const form_depart = document.getElementById('geosearch_depart')
const input_dep = form_depart.querySelector('input[type="text"]');

form_depart.addEventListener('submit', async (event) => {
  event.preventDefault();
  const results = await OSMprovider.search({ query: input_dep.value });
  lon = results[0]['x'] // take the first result (if many results)
  lat = results[0]['y'] // take the first result (if many results)
  // Put a marker on the adresse
  L.marker([lat,lon], {icon: icone_depart}).addTo(map)
    
});

// For destination
// Geosearching for start
const form_dest = document.getElementById('geosearch_dest')
const input_dest = form_dest.querySelector('input[type="text"]');

form_dest.addEventListener('submit', async (event) => {
  event.preventDefault();
  const results = await OSMprovider.search({ query: input_dest.value });
  lon = results[0]['x'] // take the first result (if many results)
  lat = results[0]['y'] // take the first result (if many results)
  console.log(lon,lat)
  L.marker([lat,lon], {icon: icone_dest}).addTo(map)
});


/* 
var popup = L.popup()
    .setLatLng([46.516662, 6.627789])
    .setContent("I am a standalone popup.")
    .openOn(map);

function onMapClick(e) {
    popup
        .setLatLng(e.latlng)
        .setContent("You clicked the map at " + e.latlng.toString())
        .openOn(map);
} */

// On ajoute la frontière de Lausanne sur le fond de carte


