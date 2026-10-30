/* ============================================================================
   static/js/weather.js           (Raidah: Destinations / Map / Weather)

   FRONTEND part of the weather feature: draws the 7-day weather card.

   HOW THE DATA ARRIVES (the whole weather pipeline):
   this file --GET /api/destinations/<id>/weather/--> Django (api_views.py)
     -> services/weather.py checks the WeatherCache table in PostgreSQL
          * data younger than 3 hours?  -> reuse it (no outside call)
          * otherwise                   -> ask Open-Meteo, save it, use it
     -> JSON comes back here -> we turn it into 7 small cards.
   The browser never talks to Open-Meteo directly: only our Django backend does.
   ============================================================================ */
const WeatherCard = (function () {
  const { el, svg, api } = DestUtils;

  // The HTML elements this file controls (they are defined in weather_card.html).
  const subtitleEl = document.getElementById('weather-subtitle');
  const updatedEl = document.getElementById('weather-updated');
  const messageEl = document.getElementById('weather-message');
  const daysEl = document.getElementById('weather-days');

  // If the user clicks two destinations quickly, the first answer could arrive
  // AFTER the second one. We number each request and ignore outdated answers.
  let latestRequest = 0;

  // Icon drawings (hard-coded by us) and their colours.
  const ICONS = {
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    cloud: '<path d="M17.5 19H9a7 7 0 1 1 6.7-9h1.8a4.5 4.5 0 1 1 0 9z"/>',
    rain: '<path d="M4 14.9A7 7 0 1 1 15.7 8h1.8a4.5 4.5 0 0 1 2.5 8.2"/><path d="M16 14v6M8 14v6M12 16v6"/>',
    snow: '<path d="M4 14.9A7 7 0 1 1 15.7 8h1.8a4.5 4.5 0 0 1 2.5 8.2"/><path d="M8 15h.01M8 19h.01M12 17h.01M12 21h.01M16 15h.01M16 19h.01"/>',
    storm: '<path d="M6 16.3A7 7 0 1 1 15.7 8h1.8a4.5 4.5 0 0 1 .5 9"/><path d="m13 12-3 5h4l-3 5"/>',
    drop: '<path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/>',
  };
  const ICON_COLORS = {
    sun: 'text-amber-500', cloud: 'text-slate-500', rain: 'text-blue-600',
    snow: 'text-sky-500', storm: 'text-violet-600',
  };

  // Our backend turns Open-Meteo's weather codes into words such as "Light rain".
  // Here we pick an icon by looking for key words in that text.
  function iconFor(condition) {
    const text = condition.toLowerCase();
    if (text.includes('thunder')) return 'storm';
    if (text.includes('snow')) return 'snow';
    if (text.includes('rain') || text.includes('drizzle') || text.includes('shower')) return 'rain';
    if (text.includes('clear')) return 'sun';
    return 'cloud'; // partly cloudy, overcast, fog ...
  }

  // "2026-10-25T10:00:00Z" -> "2 hours ago". Shows the user the data is cached.
  function timeAgo(isoString) {
    const minutes = Math.round((Date.now() - new Date(isoString).getTime()) / 60000);
    if (minutes < 1) return 'just now';
    if (minutes < 60) return minutes + ' min ago';
    if (minutes < 1440) return Math.round(minutes / 60) + ' h ago';
    return Math.round(minutes / 1440) + ' d ago';
  }

  // Builds the card for ONE day of forecast.
  // `day` is one object from the API, e.g.
  // { forecast_date: "2026-10-26", temp_max: 22, temp_min: 16,
  //   condition: "Partly cloudy", rain_probability: 20, fetched_at: "..." }
  function dayCell(day, isToday) {
    // The date is read as local midnight so it never slips to the wrong day.
    const date = new Date(day.forecast_date + 'T00:00:00');
    const box = isToday ? 'border-blue-200 bg-blue-50' : 'border-slate-200 bg-slate-50';
    const cell = el('div', 'flex flex-col items-center gap-1 rounded-xl border p-3 text-center ' + box);

    cell.appendChild(el('div', 'text-xs font-bold',
      isToday ? 'Today' : date.toLocaleDateString('en-US', { weekday: 'short' })));
    cell.appendChild(el('div', 'text-xs text-slate-500',
      date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })));

    const kind = iconFor(day.condition);
    cell.appendChild(svg(ICONS[kind], 'my-1 h-8 w-8 ' + ICON_COLORS[kind]));

    cell.appendChild(el('div', 'min-h-[2rem] text-xs text-slate-600', day.condition));
    cell.appendChild(el('div', 'text-base font-bold', Math.round(day.temp_max) + '°'));
    cell.appendChild(el('div', 'text-xs text-slate-500', Math.round(day.temp_min) + '°'));

    // Chance of rain (the API can send null when Open-Meteo has no value).
    const rain = el('div', 'mt-1 flex items-center gap-1 text-xs font-semibold text-blue-700');
    rain.appendChild(svg(ICONS.drop, 'h-3 w-3'));
    rain.appendChild(document.createTextNode(
      day.rain_probability === null ? '–' : day.rain_probability + '%'));
    cell.appendChild(rain);

    return cell;
  }

  // Shows (or hides, when text is empty) the one-line status message.
  function setMessage(text) {
    messageEl.textContent = text;
    messageEl.classList.toggle('hidden', !text);
  }

  // PUBLIC: show(destination) loads and draws the forecast for one saved destination.
  async function show(destination) {
    const myRequest = ++latestRequest;
    subtitleEl.textContent = (destination.country
      ? destination.name + ', ' + destination.country
      : destination.name) + ' · next 7 days';
    updatedEl.classList.add('hidden');
    daysEl.replaceChildren();
    setMessage('Loading weather…');

    try {
      const days = await api('/api/destinations/' + destination.id + '/weather/');
      if (myRequest !== latestRequest) return; // a newer click replaced this one

      setMessage(days.length ? '' : 'No forecast available for this place.');
      // The first item is the destination's own "today" (Open-Meteo uses the local timezone).
      days.forEach((day, index) => daysEl.appendChild(dayCell(day, index === 0)));

      if (days.length) {
        // The newest fetched_at tells us how old the cached data is.
        const newest = days.map((d) => d.fetched_at).sort().pop();
        updatedEl.textContent = 'Updated ' + timeAgo(newest);
        updatedEl.classList.remove('hidden');
      }
    } catch (error) {
      if (myRequest !== latestRequest) return;
      setMessage(error.message); // e.g. "Weather service is unavailable. Try again shortly."
    }
  }

  // PUBLIC: clear() puts the card back to its empty state.
  function clear() {
    latestRequest++; // ignore any request that is still on its way
    subtitleEl.textContent = 'Select a saved destination';
    updatedEl.classList.add('hidden');
    daysEl.replaceChildren();
    setMessage('Select a saved destination to see its 7-day forecast.');
  }

  return { show, clear };
})();