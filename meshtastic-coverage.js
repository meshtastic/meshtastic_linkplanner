var currentMarker = null;

var OpenStreetMap = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  noWrap: true, //this is the crucial line!
  bounds: [
    [-90, -180],
    [90, 180],
  ],
  attribution: "© OpenStreetMap contributors",
});

var OpenTopoMap = L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", {
  maxZoom: 17,
  noWrap: true, //this is the crucial line!
  bounds: [
    [-90, -180],
    [90, 180],
  ],
  attribution:
    'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)',
});

var map = L.map("map", {
  center: [51, -114], // Set your desired center coordinates
  zoom: 10,
  layers: [OpenStreetMap], // Set the default base layer
});

// Create a base layers object to hold the map options
var baseMaps = {
  OpenStreetMap: OpenStreetMap,
  OpenTopoMap: OpenTopoMap,
};

// Add the layer control to the map
L.control.layers(baseMaps, {}, { position: "topleft" }).addTo(map);

// add location control to the map
L.control
  .locate({
    strings: {
      title: "My Location",
    },
    locateOptions: {
      maxZoom: 10,
    },
  })
  .addTo(map);

map.on("click", function (e) {
  document.getElementById("lat").value = e.latlng.wrap().lat.toFixed(6);
  document.getElementById("lng").value = e.latlng.wrap().lng.toFixed(6);

  if (currentMarker) {
    map.removeLayer(currentMarker);
  }

  currentMarker = L.marker(e.latlng).addTo(map);
});

document.getElementById("override-checkbox").addEventListener("change", function () {
  const isEnabled = this.checked;
  document.getElementById("tx_power").disabled = !isEnabled;
  document.getElementById("frequency").disabled = !isEnabled;
});

map.on("locationfound", function (e) {
  const userLat = e.latitude;
  const userLng = e.longitude;

  // Set the latitude and longitude input values
  document.getElementById("lat").value = userLat.toFixed(6);
  document.getElementById("lng").value = userLng.toFixed(6);

  // Update marker position
  if (currentMarker) {
    map.removeLayer(currentMarker);
  }

  currentMarker = L.marker(e.latlng).addTo(map);
});

async function predict() {
  const runButton = document.querySelector("button");
  runButton.textContent = "Running Model...";
  runButton.disabled = true;

  var lat = parseFloat(document.getElementById("lat").value);
  var lon = parseFloat(document.getElementById("lng").value);
  var txh = parseFloat(document.getElementById("height").value);
  var gain = parseFloat(document.getElementById("gain").value);
  var region = document.getElementById("region").value;
  var rx_height = parseFloat(document.getElementById("rx_height").value);
  var rx_gain = parseFloat(document.getElementById("rx_gain").value);

  var postData = {
    lat: lat,
    lon: lon,
    txh: txh,
    rxh: rx_height,
    tx_gain: gain,
    rx_gain: rx_gain,
    region: region,
    resolution: 8,
  };

  if (document.getElementById("override-checkbox").checked) {
    postData.tx_power = parseFloat(document.getElementById("tx_power").value);
    postData.frequency = parseFloat(document.getElementById("frequency").value);

    postData.additional_loss = parseFloat(document.getElementById("additional_loss").value);
    postData.rx_sensitivity = parseFloat(document.getElementById("rx_sensitivity").value);
  }

  console.log("Request data:", postData);

  try {
    const response = await fetch("http://meshtastic.mpatrick.dev/predict", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(postData),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const geojson = await response.json();
    plotH3Tiles(geojson);
  } catch (error) {
    console.error("Error during prediction:", error);
  } finally {
    runButton.textContent = "Run Model";
    runButton.disabled = false;
  }
}

function plotH3Tiles(geojson) {
  if (window.h3LayerGroup) {
    map.removeLayer(window.h3LayerGroup);
  }

  const h3LayerGroup = L.layerGroup();
  const rssiThreshold = parseFloat(document.getElementById("rx_sensitivity").value);

  geojson.features.forEach((feature) => {
    const modelRssi = feature.properties.model_rssi;

    if (modelRssi > rssiThreshold) {
      const hexBoundary = feature.geometry.coordinates[0].map((coord) => [coord[1], coord[0]]);

      const color = getColorForRssi(modelRssi);

      const polygon = L.polygon(hexBoundary, {
        color: color,
        fillOpacity: 0.5,
      });

      polygon.bindTooltip(`${modelRssi.toFixed(2)} dBm`, {
        permanent: false,
        direction: "center",
      });

      h3LayerGroup.addLayer(polygon);
    }
  });

  h3LayerGroup.addTo(map);
  window.h3LayerGroup = h3LayerGroup;
}

function getColorForRssi(rssi) {
  const minRssi = -140;
  const maxRssi = -90;
  const normalized = (rssi - minRssi) / (maxRssi - minRssi);
  return d3.scaleSequential(d3.interpolatePlasma)(normalized);
}

function updateColorBar() {
  const colorBar = document.getElementById("color-bar");
  let gradientStops = [];
  const numSteps = 64;

  for (let i = 0; i <= numSteps; i++) {
    const normalized = i / numSteps;
    const color = d3.scaleSequential(d3.interpolatePlasma)(normalized);
    gradientStops.push(`${color} ${(i / numSteps) * 100}%`);
  }

  const gradient = `linear-gradient(to right, ${gradientStops.join(", ")})`;
  colorBar.style.background = gradient;
}

updateColorBar();

function openAboutDialog() {
  document.getElementById("about-dialog").showModal();
}

function closeAboutDialog() {
  document.getElementById("about-dialog").close();
}

const container = document.querySelector(".controls");
const header = document.querySelector(".controls-header");

function onMouseDrag({ movementX, movementY }) {
  let getContainerStyle = window.getComputedStyle(container);
  let leftValue = parseInt(getContainerStyle.left);
  let topValue = parseInt(getContainerStyle.top);
  container.style.left = `${leftValue + movementX}px`;
  container.style.top = `${topValue + movementY}px`;
}

header.addEventListener("mousedown", () => {
  document.addEventListener("mousemove", onMouseDrag);
});

document.addEventListener("mouseup", () => {
  document.removeEventListener("mousemove", onMouseDrag);
});
