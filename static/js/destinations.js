/* ============================================================================
   static/js/destinations.js      (Raidah: Destinations / Map / Weather)

   The "conductor" of the page. It connects the search box, the saved list,
   the map (map.js) and the weather card (weather.js).

   WHAT HAPPENS WHEN THE USER:
   - types a place and presses Search -> GET /api/destinations/search/?q=...
        Django asks OpenStreetMap's geocoder (Nominatim) for coordinates.
        Nothing is saved yet; we show the results and preview one on the map.
   - presses Save                      -> POST /api/destinations/
        Django stores the destination in PostgreSQL (Destination table).
   - clicks a saved destination        -> map flies there + weather card loads
        (GET /api/destinations/<id>/weather/)
   - presses the bin icon              -> DELETE /api/destinations/<id>/
   ============================================================================ */
(function () {
  const { el, svg, api } = DestUtils;

  const API = '/api/destinations/';
  const page = document.getElementById('dest-page');
  // Address of Member 3's itinerary-stops API. It is set in views.py and is
  // empty until Member 3's endpoint exists.
  const STOPS_URL = page.dataset.stopsUrl;

  // The HTML elements we control (defined in search.html).
  const form = document.getElementById('search-form');
  const input = document.getElementById('search-input');
  const searchButton = document.getElementById('search-button');
  const messageBox = document.getElementById('dest-message');
  const resultsList = document.getElementById('results');
  const resultsCount = document.getElementById('results-count');
  const savedList = document.getElementById('saved-list');
  const savedCount = document.getElementById('saved-count');

  // The page's memory:
  let saved = [];         // destinations stored in the database
  let selected = null;    // the saved destination the user is looking at
  let lastResults = [];   // the latest search results

  // Icon drawings (hard-coded markup).
  const PIN_ICON = '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>';
  const TRASH_ICON = '<path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>';
  const PLUS_ICON = '<path d="M5 12h14M12 5v14"/>';
  const CHECK_ICON = '<path d="M20 6 9 17l-5-5"/>';

  function showMessage(text) {
    messageBox.textContent = text || '';
  }

  // ---------------------------------------------------------------------------
  // SEARCH RESULTS
  // ---------------------------------------------------------------------------

  // Is this search result already in our saved list? (same name and nearly the same coordinates)
  function isAlreadySaved(place) {
    return saved.some((d) =>
      d.name === place.name &&
      Math.abs(d.latitude - place.latitude) < 0.01 &&
      Math.abs(d.longitude - place.longitude) < 0.01);
  }

  function makeSaveButton(place) {
    const button = el('button', 'flex items-center gap-1.5 whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-semibold');
    button.type = 'button';
    if (isAlreadySaved(place)) {
      button.className += ' bg-emerald-50 text-emerald-700';
      button.disabled = true;
      button.append(svg(CHECK_ICON, 'h-3.5 w-3.5'), 'Saved');
    } else {
      button.className += ' bg-blue-50 text-blue-700 hover:bg-blue-100';
      button.append(svg(PLUS_ICON, 'h-3.5 w-3.5'), 'Save');
      button.addEventListener('click', () => saveDestination(place));
    }
    return button;
  }

  function renderResults() {
    resultsList.replaceChildren();
    resultsCount.textContent = lastResults.length
      ? lastResults.length + (lastResults.length === 1 ? ' RESULT' : ' RESULTS')
      : '';
    lastResults.forEach((place) => {
      const row = el('li', 'flex items-center justify-between gap-3 border-t border-slate-100 py-3');

      // Clicking the name/address previews the place on the map (without saving).
      const info = el('button', 'min-w-0 flex-1 text-left');
      info.type = 'button';
      info.appendChild(el('div', 'truncate text-sm font-semibold', place.name));
      info.appendChild(el('div', 'truncate text-xs text-slate-500', place.display_name));
      info.addEventListener('click', () => TripMap.showPreview(place));

      row.append(info, makeSaveButton(place));
      resultsList.appendChild(row);
    });
  }

  // The search form was submitted.
  form.addEventListener('submit', async (event) => {
    event.preventDefault(); // stop the browser from reloading the page
    showMessage('');
    const query = input.value.trim();
    if (query.length < 2) {
      showMessage('Type at least 2 characters.');
      return;
    }

    searchButton.disabled = true;
    searchButton.textContent = 'Searching…';
    try {
      // We search only when the user presses Search (never "as you type") because
      // the free Nominatim service allows about 1 request per second.
      lastResults = await api(API + 'search/?q=' + encodeURIComponent(query));
      renderResults();
      if (lastResults.length > 0) TripMap.showPreview(lastResults[0]);
      else showMessage('No places found. Try a different spelling.');
    } catch (error) {
      showMessage(error.message);
    } finally {
      searchButton.disabled = false;
      searchButton.textContent = 'Search';
    }
  });

  // ---------------------------------------------------------------------------
  // SAVED DESTINATIONS
  // ---------------------------------------------------------------------------

  function renderSaved() {
    savedList.replaceChildren();
    savedCount.textContent = saved.length + ' saved';
    if (saved.length === 0) {
      savedList.appendChild(el('li', 'text-sm text-slate-500',
        'Nothing saved yet. Search for a place above and press Save.'));
      return;
    }

    saved.forEach((d) => {
      const isSelected = selected !== null && selected.id === d.id;
      const row = el('li', 'flex items-center gap-2 rounded-xl border p-2 ' +
        (isSelected ? 'border-blue-300 bg-blue-50' : 'border-slate-200 bg-white'));

      // The main part of the row: click to select (map flies there, weather loads).
      const select = el('button', 'flex min-w-0 flex-1 items-center gap-3 text-left');
      select.type = 'button';
      const iconBox = el('span', 'flex h-9 w-9 flex-none items-center justify-center rounded-lg ' +
        (isSelected ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-600'));
      iconBox.appendChild(svg(PIN_ICON, 'h-[18px] w-[18px]'));
      const text = el('span', 'min-w-0');
      text.appendChild(el('span', 'block truncate text-sm font-semibold',
        d.country ? d.name + ', ' + d.country : d.name));
      text.appendChild(el('span', 'block text-xs text-slate-500',
        d.latitude.toFixed(2) + ', ' + d.longitude.toFixed(2)));
      select.append(iconBox, text);
      select.addEventListener('click', () => selectDestination(d));

      const remove = el('button', 'flex h-8 w-8 flex-none items-center justify-center rounded-lg text-red-600 hover:bg-red-50');
      remove.type = 'button';
      remove.setAttribute('aria-label', 'Remove ' + d.name);
      remove.appendChild(svg(TRASH_ICON, 'h-4 w-4'));
      remove.addEventListener('click', () => deleteDestination(d));

      row.append(select, remove);
      savedList.appendChild(row);
    });
  }

  // Load all saved destinations from the database and refresh list + map pins.
  async function loadSaved() {
    const data = await api(API);
    // If someone later turns on DRF pagination, the list arrives inside data.results.
    saved = Array.isArray(data) ? data : data.results;
    renderSaved();
    TripMap.setSavedDestinations(saved, selected ? selected.id : null, selectDestination);
  }

  // The user picked a saved destination: highlight it, move the map, load the weather.
  function selectDestination(destination) {
    selected = destination;
    renderSaved();
    TripMap.setSavedDestinations(saved, destination.id, selectDestination);
    TripMap.clearPreview(); // the real pin replaces the temporary one
    TripMap.flyTo(destination.latitude, destination.longitude);
    WeatherCard.show(destination);
  }

  // Save a search result: POST it to Django, which stores it in PostgreSQL.
  async function saveDestination(place) {
    showMessage('');
    try {
      const created = await api(API, {
        method: 'POST',
        body: JSON.stringify({
          name: place.name,
          country: place.country,
          latitude: place.latitude,
          longitude: place.longitude,
          // TODO (after Member 1's Trip model is merged): also send the trip id here.
        }),
      });
      await loadSaved();
      renderResults();             // flips this result's button to "Saved"
      selectDestination(created);
    } catch (error) {
      showMessage(error.message);
    }
  }

  async function deleteDestination(destination) {
    if (!confirm('Remove ' + destination.name + ' from your saved destinations?')) return;
    showMessage('');
    try {
      await api(API + destination.id + '/', { method: 'DELETE' });
      if (selected && selected.id === destination.id) {
        selected = null;
        WeatherCard.clear();
      }
      await loadSaved();
      renderResults();
    } catch (error) {
      showMessage(error.message);
    }
  }

  // ---------------------------------------------------------------------------
  // ITINERARY STOPS (created by Member 3, only displayed here)
  // ---------------------------------------------------------------------------

  // Sample stops (Alimul's Tokyo itinerary, approximate coordinates) so the map can be
  // demonstrated BEFORE Member 3's API exists. Open the page with ?demo=1 to see them.
  const DEMO_STOPS = [
    { title: 'Check-in at Hotel Gracery Shinjuku', day: 1, order: 1, latitude: 35.6957, longitude: 139.7010, start_time: '15:00', category: 'Accommodations' },
    { title: 'Omoide Yokocho Yakitori Dinner', day: 1, order: 2, latitude: 35.6930, longitude: 139.6996, start_time: '18:30', category: 'Food' },
    { title: 'Tokyo Metropolitan Observation Deck', day: 1, order: 3, latitude: 35.6896, longitude: 139.6921, start_time: '20:30', category: 'Sightseeing' },
    { title: 'Senso-ji Temple Morning Visit', day: 2, order: 1, latitude: 35.7148, longitude: 139.7967, start_time: '09:00', category: 'Sightseeing' },
    { title: 'Unagi Eel Lunch in Asakusa', day: 2, order: 2, latitude: 35.7125, longitude: 139.7955, start_time: '12:30', category: 'Food' },
    { title: 'Akihabara Electric Town', day: 2, order: 3, latitude: 35.6984, longitude: 139.7731, start_time: '14:30', category: 'Activities' },
  ];

  async function loadStops() {
    try {
      let stops = [];
      if (STOPS_URL) {
        const data = await api(STOPS_URL);
        stops = Array.isArray(data) ? data : data.results;
      } else if (new URLSearchParams(window.location.search).get('demo') === '1') {
        stops = DEMO_STOPS;
      }
      TripMap.setStops(stops);
    } catch (error) {
      showMessage('Could not load itinerary stops: ' + error.message);
    }
  }

  // ---------------------------------------------------------------------------
  // START-UP: runs once when the page opens
  // ---------------------------------------------------------------------------
  TripMap.init();
  loadStops();
  loadSaved()
    .then(() => { if (saved.length > 0) selectDestination(saved[0]); }) // newest first
    .catch((error) => showMessage(error.message));
})();