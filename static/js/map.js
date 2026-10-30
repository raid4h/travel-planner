/* ============================================================================
   static/js/map.js               (Raidah: Destinations / Map / Weather)

   FRONTEND part of the map feature, built with Leaflet (a free map library)
   and OpenStreetMap (the free map pictures, called "tiles").

   The map shows TWO kinds of things:
     1. Saved destinations   -> round pins (the selected one is blue and bigger)
     2. Itinerary stops      -> numbered coloured circles joined by a dashed line,
                                one colour per day. These stops are CREATED by
                                Member 3's AI itinerary; this file only DISPLAYS them.

   This file only draws. It does not talk to the server. destinations.js
   gives it the data and calls the PUBLIC functions at the bottom.

   Shape of one itinerary stop (what Member 3's API must send us):
     { title: "Senso-ji Temple", day: 2, order: 1, latitude: 35.7148,
       longitude: 139.7967, start_time: "09:00", category: "Sightseeing" }
   ============================================================================ */
const TripMap = (function () {
  const { el } = DestUtils;

  // One colour per itinerary day (Day 1 = blue, Day 2 = purple ...). Repeats after 5 days.
  const DAY_COLORS = ['#2563EB', '#7C3AED', '#0D9488', '#D97706', '#DB2777'];

  let map;                  // the Leaflet map object
  let savedLayer;           // a "layer group" = a box holding all the saved-destination pins
  let stopsLayer;           // a layer group holding itinerary markers and route lines
  let previewMarker = null; // temporary marker for the search result being looked at
  let allStops = [];        // every itinerary stop we were given
  let selectedDay = 'all';  // which day the chips currently filter to ('all' or a number)

  function colorForDay(day) {
    return DAY_COLORS[(Number(day) - 1) % DAY_COLORS.length] || DAY_COLORS[0];
  }

  // ---- Marker icons (small coloured HTML shapes instead of image files) -----------
  function pinIcon(isSelected) {
    const size = isSelected ? 22 : 16;
    const color = isSelected ? 'bg-blue-600' : 'bg-slate-800';
    return L.divIcon({
      className: '', // removes Leaflet's default white square around divIcons
      html: '<div style="width:' + size + 'px;height:' + size + 'px" ' +
            'class="rounded-full border-2 border-white shadow-md ' + color + '"></div>',
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2], // the middle of the circle sits on the coordinates
    });
  }

  function previewIcon() {
    return L.divIcon({
      className: '',
      html: '<div style="width:18px;height:18px" ' +
            'class="rounded-full border-2 border-white bg-amber-500 shadow-md"></div>',
      iconSize: [18, 18],
      iconAnchor: [9, 9],
    });
  }

  function numberIcon(number, color) {
    return L.divIcon({
      className: '',
      html: '<div style="background:' + color + ';width:28px;height:28px" ' +
            'class="flex items-center justify-center rounded-full border-2 border-white ' +
            'text-xs font-bold text-white shadow-md">' + number + '</div>',
      iconSize: [28, 28],
      iconAnchor: [14, 14],
    });
  }

  // The small white box that opens when you click an itinerary marker.
  // Built with el() (textContent), so an AI-written title cannot inject HTML.
  function stopPopup(stop) {
    const box = el('div', 'text-sm');
    box.appendChild(el('div', 'font-bold', stop.title));
    const details = ['Day ' + stop.day];
    if (stop.start_time) details.push(stop.start_time);
    if (stop.category) details.push(stop.category);
    box.appendChild(el('div', 'mt-1 text-xs text-slate-600', details.join(' · ')));
    return box;
  }

  // ---- Day filter chips ("All days", "Day 1", "Day 2" ...) ------------------------
  function makeChip(value, label) {
    const isActive = String(value) === String(selectedDay);
    const button = el('button',
      'flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold ' +
      (isActive ? 'border-slate-900 bg-slate-900 text-white'
                : 'border-slate-300 bg-white text-slate-900 hover:bg-slate-50'),
      label);
    button.type = 'button';
    if (value !== 'all') {
      const dot = el('span', 'h-2 w-2 rounded-full');
      dot.style.background = colorForDay(value);
      button.prepend(dot);
    }
    button.addEventListener('click', () => {
      selectedDay = value;
      renderDayChips();
      renderStops(true);
    });
    return button;
  }

  function renderDayChips() {
    const box = document.getElementById('day-chips');
    box.replaceChildren();
    // Hide the "no stops" hint as soon as we have at least one stop.
    document.getElementById('stops-empty').classList.toggle('hidden', allStops.length > 0);
    // The unique day numbers, sorted: [1, 2, 3]
    const days = [...new Set(allStops.map((s) => s.day))].sort((a, b) => a - b);
    if (days.length === 0) return;
    box.appendChild(makeChip('all', 'All days'));
    days.forEach((day) => box.appendChild(makeChip(day, 'Day ' + day)));
  }

  // Draws the itinerary stops for the selected day(s).
  function renderStops(fitToView) {
    stopsLayer.clearLayers();
    const visible = allStops.filter(
      (s) => selectedDay === 'all' || String(s.day) === String(selectedDay));

    // Group the stops by day: { 1: [stop, stop, stop], 2: [...] }
    const byDay = {};
    visible.forEach((s) => { (byDay[s.day] = byDay[s.day] || []).push(s); });

    Object.keys(byDay).forEach((day) => {
      const color = colorForDay(day);
      const list = byDay[day].sort((a, b) => (a.order || 0) - (b.order || 0));

      // A dashed line joining the day's stops in order.
      L.polyline(list.map((s) => [s.latitude, s.longitude]),
        { color: color, weight: 3, opacity: 0.8, dashArray: '7 6' }).addTo(stopsLayer);

      // One numbered circle per stop: 1, 2, 3 ... within its day.
      list.forEach((stop, index) => {
        L.marker([stop.latitude, stop.longitude], { icon: numberIcon(index + 1, color) })
          .bindPopup(stopPopup(stop))
          .addTo(stopsLayer);
      });
    });

    if (fitToView && visible.length > 0) {
      // Zoom and move the map so every visible stop fits on screen.
      map.fitBounds(visible.map((s) => [s.latitude, s.longitude]),
        { padding: [40, 40], maxZoom: 14 });
    }
  }

  function setLayerVisible(layer, visible) {
    if (visible) map.addLayer(layer);
    else map.removeLayer(layer);
  }

  // =================== PUBLIC FUNCTIONS (used by destinations.js) ===================

  // init(): creates the map. Call once, after the page has loaded.
  function init() {
    // 'map' is the id of the <div> in map.html. [20, 0] with zoom 2 = whole-world view.
    map = L.map('map').setView([20, 0], 2);

    // The map pictures come from OpenStreetMap. The attribution text is REQUIRED by their licence.
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors',
      // OpenStreetMap BLOCKS tile requests that arrive without a "Referer" header.
      // Django's default security setting tells the browser not to send one to other
      // websites, so we override that for the map tiles only.
      referrerPolicy: 'strict-origin-when-cross-origin',
    }).addTo(map);

    savedLayer = L.layerGroup().addTo(map);
    stopsLayer = L.layerGroup().addTo(map);

    // The two checkboxes above the map switch each group on and off.
    document.getElementById('toggle-saved').addEventListener('change',
      (event) => setLayerVisible(savedLayer, event.target.checked));
    document.getElementById('toggle-stops').addEventListener('change',
      (event) => setLayerVisible(stopsLayer, event.target.checked));
  }

  // setSavedDestinations(): redraws the pins for the saved destinations.
  // onSelect is a function we call when the user clicks a pin.
  function setSavedDestinations(destinations, selectedId, onSelect) {
    savedLayer.clearLayers();
    destinations.forEach((d) => {
      L.marker([d.latitude, d.longitude], { icon: pinIcon(d.id === selectedId), title: d.name })
        .bindTooltip(el('span', '', d.name)) // hover label
        .on('click', () => onSelect(d))
        .addTo(savedLayer);
    });
  }

  // showPreview(): drops a temporary amber marker on a SEARCH RESULT (not saved yet).
  function showPreview(place) {
    clearPreview();
    previewMarker = L.marker([place.latitude, place.longitude], { icon: previewIcon() })
      .bindPopup(el('div', 'text-sm font-semibold', place.name))
      .addTo(map)
      .openPopup();
    map.flyTo([place.latitude, place.longitude], 10);
  }

  function clearPreview() {
    if (previewMarker) {
      map.removeLayer(previewMarker);
      previewMarker = null;
    }
  }

  function flyTo(latitude, longitude, zoom) {
    map.flyTo([latitude, longitude], zoom || 10); // smooth animated move
  }

  // setStops(): gives the map the itinerary stops to display.
  function setStops(stops) {
    allStops = stops;
    selectedDay = 'all';
    renderDayChips();
    renderStops(true);
  }

  return { init, setSavedDestinations, showPreview, clearPreview, flyTo, setStops };
})();