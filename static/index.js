// Setting geosearch control for geocoding 
var GeoSearchControl = window.GeoSearch.GeoSearchControl;
var OpenStreetMapProvider = window.GeoSearch.OpenStreetMapProvider;

// Create icons for start/destination markers
const icone_depart = L.icon({
    iconUrl: 'static/img/marker_dep.svg',
    iconSize: [35,95],
    iconAnchor:   [22, 94], // point of the icon which will correspond to marker's location
    popupAnchor:  [-3, -76] // point from which the popup should open relative to the iconAnchor
});
const icone_dest = L.icon({
    iconUrl: 'static/img/marker_destination.svg', 
    iconSize: [35,95],
    iconAnchor:   [22, 94], // point of the icon which will correspond to marker's location
    });

// Initialize map and center view on Lausanne
var map = L.map('map').setView([46.5, 6.6], 13);

const provider = new OpenStreetMapProvider({
  params: {
    'accept-language': 'fr', // render results in French
    countrycodes: 'ch', // limit search results to the Switzerland
  },
});

const searchControl = new GeoSearchControl({
  provider: provider,
  style: 'button',
  searchLabel: 'Entrez votre adresse',
  autoClose: true
});

map.addControl(searchControl);
map.setMinZoom(7)


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

OpenStreetMap_CH.addTo(map)
L.control.layers(baseLayers).addTo(map)

// Interactivity about gelocalisation 
// 1st possibility : click on a button
// Deal with the event 
L.DomEvent.on(document.getElementById('btnGetLoc'), 'click', function(){
  map.locate({setView: true, maxZoom: 16});
})
// Display marker at localisation 
function onLocationFound(e) {
  var radius = e.accuracy;
  L.marker(e.latlng).addTo(map)
      .bindPopup("You are within " + radius + " meters from this point. Its coordiantes are" + e.latlng).openPopup();
  L.circle(e.latlng, radius).addTo(map);
};

// Add it to the map
map.on('locationfound', onLocationFound);

// 2nd possiblity : click on the map : it creates a marker
//newMarkerGroup = new L.LayerGroup();
//map.on('click', addMarker);

var marker_depart = new L.marker([46.516662, 6.627789], {icon:icone_depart}).addTo(map);
var marker_destination = new L.marker([47.5, 7.5], {icon:icone_dest}).addTo(map);

function addMarker(e){
// Add marker to map at click location; add popup window
    newMarker
        .setLatLng(e.latlng) 
        .addTo(map);
}

var popup = L.popup()
    .setLatLng([46.516662, 6.627789])
    .setContent("I am a standalone popup.")
    .openOn(map);

function onMapClick(e) {
    popup
        .setLatLng(e.latlng)
        .setContent("You clicked the map at " + e.latlng.toString())
        .openOn(map);
}

map.on('click', onMapClick);

// On ajoute la frontière de Lausanne sur le fond de carte


