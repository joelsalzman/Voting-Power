// Useful variables
var vh = $(window).height();
var vw = $(window).width();
var isMobile = vh > vw;
var field = "rawUtility";
var scheme = "multichrome";
var tooltipButton = document.getElementById("button-tooltip");

// Set up the map
var map  = (isMobile) ? L.map('gdvp-map').setView([20, -99], 5) : L.map('gdvp-map').setView([38, -93], 4);
var gdvp = document.getElementById("gdvp-map");

// Fields
var fieldDict = {
  "rawUtility": {
    name:    "Overall Relative Voting Power",
    title:   "Overall Relative<br>Voting Power",
    range:   [.4, .6],
    labels:  ["0.4 (Blowouts)", "1.0 (Ties)"],
    flip:    false,
    display: function(val) { return String(val).slice(0, 6); }
  },
  "decUtility": {
    name:    "Overall Election Competitiveness",
    title:   "Overall Election<br>Competitiveness",
    range:   [.4, .6],
    labels:  ["0.4 (Safe)", "1.0 (Swing)"],
    flip:    false,
    display: function(val) { return String(val).slice(0, 6); }
  },
  "h_rawMargin_avg": {
    name:    "House Average Raw Margin",
    title:   "House Average<br>Raw Margin",
    range:   [17193, 192181],
    labels:  ["192,181 Votes", "17,193 Votes"],
    flip:    true,
    display: function(val) { return parseInt(val).toLocaleString() + " Votes"; }
  },
  "s_rawMargin_avg": {
    name:    "Senate Average Raw Margin",
    title:   "Senate Average<br>Raw Margin",
    range:   [38699, 2064244],
    labels:  ["2,064,224 Votes", "38,699 Votes"],
    flip:    true,
    display: function(val) { return parseInt(val).toLocaleString() + " Votes"; }
  },
  "p_rawMargin_avg": {
    name:    "Presidential Average Raw Margin",
    title:   "Presidential<br>Average Raw Margin",
    range:   [25431, 2615286],
    labels:  ["2,615,286 Votes", "25,431 Votes"],
    flip:    true,
    display: function(val) { return parseInt(val).toLocaleString() + " Votes"; }
  },
  "h_decMargin_avg": {
    name:    "House Proportional Average Margin",
    title:   "House Proportional<br>Average Margin",
    range:   [0, 1],
    labels:  ["100% (Blowouts)", "0% (Ties)"],
    flip:    true,
    display: function(val) { return String(val * 100).slice(0, 7) + "%"; }
  },
  "s_decMargin_avg": {
    name:    "Senate Proportional Average Margin",
    title:   "Senate Proportional<br>Average Margin",
    range:   [0, 1],
    labels:  ["100% (Blowouts)", "0% (Ties)"],
    flip:    true,
    display: function(val) { return String(val * 100).slice(0, 7) + "%"; }
  },
  "p_decMargin_avg": {
    nname:   "Presidential Proportional Average Margin",
    title:   "Presidential Proportional<br>Average Margin",
    range:   [0, 1],
    labels:  ["100% (Blowouts)", "0% (Ties)"],
    flip:    true,
    display: function(val) { return String(val * 100).slice(0, 7) + "%"; }
  },
  "changes": {
    name:    "Number of Times Redistricted",
    title:   "Number of Times<br>Redistricted",
    range:   [0, 5],
    labels:  ["0", "5"],
    flip:    false,
  },
  "changeDesc": {
    display: function(val) { return val; }
  }
};

// Header formatting
var info = document.getElementById("gdvp-info");
var infoText = document.getElementById("gdvp-info-text");
var headerButtons = document.getElementsByClassName("gdvp-header");
formatHeader = function() {
  if (isMobile) {
    info.style.width    = 0.98 * vw + "px";
    info.style.position = "relative";
    gdvp.style.height   = .8 * vh + "px";
    document.getElementById("button-back").innerHTML = "«";
    tooltipButton.innerHTML = "≡";
    for (var i = 0; i < headerButtons.length - 1; i++) {
      headerButtons[i].style.marginLeft = "3vw";
    }
  } else {
    vw = $(window).width();
    var w = vw * 0.93;
    var m = vw * 0.03;
    for (var i = 0; i < headerButtons.length; i++) {
      let buttonLength = headerButtons[i].offsetWidth;
      w -= buttonLength;
      if (i < 2) { m += buttonLength; }
    }
    info.style.width = w + "px";
    info.style.marginLeft = m + "px";
  }
}
window.onload = formatHeader;
window.addEventListener('resize', formatHeader);
info.update = function(properties) {
  let f = (field == "changes") ? "changeDesc" : field;
  info.innerHTML = (properties) ? 
    '<h3 id="gdvp-info-text">' + fieldDict[f].display(properties[f]) + '</h3>' :
    '<h4 id="gdvp-info-text">' + fieldDict[field].name + '</h4>';
  infoText = document.getElementById("gdvp-info-text");
  if (infoText.offsetHeight > 0.9 * info.offsetHeight) {
    info.innerHTML = '<h4 id="gdvp-info-text">' + fieldDict[f].display(properties[f]) + '</h4>';
    infoText = document.getElementById("gdvp-info-text");
    if (infoText.offsetHeight > 0.6 * info.offsetHeight) {
      infoText.style.marginTop = "1vh";
    }
  }
}

// Symbologies
function colorize(val) {
  var range  = fieldDict[field].range;
  var r = 0;
  var g = 0;
  var b = 0;

  if (val || val == 0) {

    // Normalize the value
    var n = (val - range[0]) / range[1];

    // Invert the value if the field isn't Utility
    if (fieldDict[field].flip) { n = (n * -1) + 1; }

    // Set RGB values
    if (scheme == "multichrome") {
      var stops = [[150, 255, 161, 65,  44,  37], 
                   [150, 255, 218, 182, 127, 52], 
                   [0,   150, 180, 196, 184, 148]];
      var level = 1
      if (n > .8) {
        n = (n * 5) - 4;
      } else if (n > .6) {
        n = (n * 5) - 3;
        level += 1;
      } else if (n > .4) {
        n = (n * 5) - 2;
        level += 2;
      } else if (n > .2) {
        n = (n * 5) - 1;
        level += 3;
      } else {
        n = n * 5;
        level += 4;
      }
      r = (n * (stops[0][level - 1] - stops[0][level])) + stops[0][level];
      g = (n * (stops[1][level - 1] - stops[1][level])) + stops[1][level];
      b = (n * (stops[2][level - 1] - stops[2][level])) + stops[2][level];
    } 
    else {
      r = b = 128 + (127 * (1 - n));
      g = 255 * (1 - n);
    }
    return "rgb(" + String(parseInt(r)) + ", " + String(parseInt(g)) + ", " + String(parseInt(b)) + ")";
  }

  // Return transparent for undefined values
  return "rgba(0, 0, 0, 0)";
}

// Interactions
function styleLayers(feat) {
  return {
    fillColor: colorize(feat.properties[field]),
    weight: 1,
    opacity: 1,
    color: 'black',
    fillOpacity: 0.75
  };
}

function showData(e) {
  var layer = e.target;
  layer.setStyle({
    weight: 2.5,
    fillOpacity: 1
  });
  info.update(layer.feature.properties);
  if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
    layer.bringToFront();
  }
}

function hideData(e) {
  e.target.setStyle({
    weight: 1,
    fillOpacity: 0.75
  });
  info.update();
}

var featureClicked = false;
function onEachFeature(feat, layer) {
  layer.on({
    mouseover: showData,
    mouseout: hideData,
    click: function(e) {
      if (isMobile) {
        (featureClicked) ? showData : hideData;
        featureClicked = !featureClicked;
      } else {
        map.fitBounds(e.target.getBounds());
      }
    }
  });
}

// Add the basemap
var OpenStreetMap_Mapnik = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
	maxZoom: 19,
	attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// Display the initial data
var lyrs = {
  'Alabama':'', 'Alaska':'', 'Arizona':'', 'Arkansas':'', 'California':'', 'Colorado':'', 
  'Connecticut':'', 'Delaware':'', 'District of Columbia':'', 'Florida':'', 'Georgia':'', 
  'Hawaii':'', 'Idaho':'', 'Illinois':'', 'Indiana':'', 'Iowa':'', 'Kansas':'', 'Kentucky':'', 
  'Louisiana':'', 'Maine':'', 'Maryland':'', 'Massachusetts':'', 'Michigan':'', 'Minnesota':'', 
  'Mississippi':'', 'Missouri':'', 'Montana':'', 'Nebraska':'', 'Nevada':'', 'New Hampshire':'', 
  'New Jersey':'', 'New Mexico':'', 'New York':'', 'North Carolina':'', 'North Dakota':'', 
  'Ohio':'', 'Oklahoma':'', 'Oregon':'', 'Pennsylvania':'', 'Rhode Island':'', 'South Carolina':'', 
  'South Dakota':'', 'Tennessee':'', 'Texas':'', 'Utah':'', 'Vermont':'', 'Virginia':'', 
  'Washington':'', 'West Virginia':'', 'Wisconsin':'', 'Wyoming':''
};

// Build the layers
buildLayer = function(st) {
  $.getJSON(
    "https://raw.githubusercontent.com/joelsalzman/joelsalzman.github.io/master/final_by_state/" 
    + st 
    + ".js", 
    function(data) {
      lyrs[st] = new L.geoJSON(data, {
        style: styleLayers,
        onEachFeature: onEachFeature
      }).addTo(map);
    }
  );
}
for (let st in lyrs) { buildLayer(st); };

// Build all the layers
rebuildLayers = function() {
  for (let st in lyrs) {
    let layer = lyrs[st];
    if (map.hasLayer(layer)) {
      map.removeLayer(layer);
      buildLayer(st);
    }
  };
  setLegend();
  info.update();
};

// Legend and scale bar
var legend   = L.control({position: "bottomleft"})
legend.onAdd = function(map) {
  var div = L.DomUtil.create("div", "control-container");
  div.innerHTML = '<div id="legend-title"></div>'  +
                  '<div class="legend-container">' +
                    '<div id="legend-bar"></div>'  +
                  '</div>' +
                  '<div class="legend-container">' +
                    '<div class="legend-key" id="key-top"></div>'    +
                    '<div class="legend-key" id="key-bottom"></div>' +
                  '</div>';
  return div;
}
legend.addTo(map);

setLegend    = function() {
  var labels = fieldDict[field].labels;
  var keys   = [document.getElementById("key-bottom"), document.getElementById("key-top")];

  document.getElementById("legend-title").innerHTML = fieldDict[field].title;
  document.getElementById("legend-bar").style.backgroundImage = (scheme == "multichrome") ?
      "linear-gradient(to bottom, rgb(150, 150, 0), rgb(255, 255, 150), " +
      "rgb(161, 218, 180), rgb(65, 182, 196), rgb(44, 127, 184), rgb(37, 52, 148))" :
      "linear-gradient(to top, rgb(255, 255, 255), rgb(127, 0, 127)";
  for (let i = 0; i < 2; i++) { keys[i].innerHTML = labels[i]; };
}
setLegend();

L.control.scale().addTo(map);

/* -------------------------------------- The tooltip -------------------------------------- */

// Toggle the tooltip
var tools   = [false, false]
var tooltip = document.getElementById("tooltip");

tooltipButton.onclick = function() {
  if (isMobile && tooltip.style.width != "70vw") {
    gdvp.style.width = "30vw";
    tooltip.style.display = "block";
    tooltip.style.width = "70vw";
  }
  else if (!isMobile && tooltip.style.width != "30%") {
    gdvp.style.width = "70vw";
    tooltip.style.display = "block";
    tooltip.style.width = "30%";
  } else {
    gdvp.style.width = "100vw";
    tooltip.style.width = "0%";
    tooltip.style.display = "none";
  }
};

// State 
checkContainer = document.getElementById("state-checks");
showAllStates  = document.getElementById("button-state");

toggleCheckContainer = function() {
  if (tools[0]) { 
    showAllStates.style.display = "none"; 
    checkContainer.style.display = "none";
  }
  else { 
    showAllStates.style.display = "block"; 
    checkContainer.style.display = "block";
  }
  tools[0] = !tools[0];
}

toggleState = function(st, mustHide=false, mustShow=false) {
  let layer = lyrs[st];
  var check = document.getElementById("check-" + st);

  // Mark or unmark the check
  if ((mustHide && check.checked)  || 
      (mustShow && !check.checked) || 
      (!mustHide && !mustShow && map.hasLayer(layer) == check.checked)) { 
    check.checked = !check.checked; 
  }
  var show  = (mustShow || (check.checked && !mustHide)) ? true : false;

  // Show or hide the layer
  if (show && !map.hasLayer(layer)) { map.addLayer(layer); }
  if (!show && map.hasLayer(layer)) { map.removeLayer(layer); }
}
allButton = true;
toggleAllStates = function() {
  for (let st in lyrs) { (allButton) ? toggleState(st, true) : toggleState(st, false, true);}
  showAllStates.innerHTML = (allButton) ? "Show All" : "Hide All";
  allButton = !allButton;
}

// Change Field
var fieldCont = document.getElementById("field-container");
var circles = $(".circle");

toggleFieldContainer = function() {
  (tools[1]) ? fieldCont.style.display="none" : fieldCont.style.display="block";
  tools[1] = !tools[1];
}

changeField = function(newField) {

  // Do nothing if the field is being set to the same thing
  if (field == newField) {
    var c = document.getElementById(field);
    c.checked = true;
    return;
  }

  // Change the field and rebuild the layers
  field = newField;
  rebuildLayers();

  // Make sure only the correct circle is marked
  circles.each(function(i) {
    let c = circles[i];
    if ((c.checked && $(c).attr("id") != field) || ($(c).attr("id") == field && !c.checked)) { 
      c.checked = !c.checked; 
    }
  });
}

// Set scheme
var setSchemeButton = document.getElementById("set-scheme");
setScheme = function() {

  // Set the scheme and the button text
  if (scheme == "multichrome") {
    scheme = "purpscale";
    setSchemeButton.innerHTML = "Set Colors to Multichrome";
  } else {
    scheme = "multichrome";
    setSchemeButton.innerHTML = "Set Colors to Monochrome";
  }

  // Recolor the layers
  rebuildLayers();
}