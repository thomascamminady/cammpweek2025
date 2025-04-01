[out:json][timeout:550];

(
// Proper roads: roads where cars can ride (and typically bikes as well).
// Only include ways that are at least 500m long.
  way["highway"~"^(residential|tertiary|secondary|primary|unclassified)$"]
  (50.72034102389627,7.098294496536256,50.722915307508394,7.10144340991974);

// Dedicated bike lanes (cycleways) at least 500m long.
  way["highway"="cycleway"](50.72034102389627,7.098294496536256,50.722915307508394,7.10144340991974);
)->.roads;

// --- Select nodes near these roads ---
// Traffic controls: traffic signals and stop signs.
node(around.roads:5)["highway"="traffic_signals"]->.traffic_lights;
node(around.roads:5)["highway"="stop"]->.stop_signs;

// --- Combine all results ---
(
  .roads;
  .barriers;
  .traffic_lights;
  .stop_signs;
);
out geom meta;
>;
out skel qt;














