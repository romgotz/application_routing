// Setting geosearch control for geocoding 
var GeoSearchControl = window.GeoSearch.GeoSearchControl;
var OpenStreetMapProvider = window.GeoSearch.OpenStreetMapProvider;

var map = L.map('map').setView([46.8, 8.15], 8);

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
	maxZoom: 18,
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

// On ajoute la frontière de Lausanne sur le fond de carte


