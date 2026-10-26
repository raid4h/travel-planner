/* ============================================================================
   static/js/dest_utils.js        (Raidah: Destinations / Map / Weather)

   WHAT THIS FILE IS
   Small helper functions shared by the other destination JavaScript files.
   Everything lives on ONE object called DestUtils, so our function names can
   never clash with names used in other members' JS files.

   LOAD ORDER (set in search.html):
   dest_utils.js -> weather.js -> map.js -> destinations.js
   ============================================================================ */
const DestUtils = (function () {
  // "(function () { ... })()" runs immediately. Variables inside it are private;
  // only what we list in the final `return { ... }` can be used by other files.

  // el(tag, classes, text) builds one HTML element.
  // We set the text with textContent (never innerHTML), so text that comes from
  // an API (place names, AI-written titles) can never inject HTML or scripts.
  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  // svg(paths, classes) builds a small inline icon.
  // `paths` is hard-coded drawing markup written by us (never user data).
  function svg(paths, className) {
    const holder = document.createElement('div');
    holder.innerHTML =
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
      'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" ' +
      'class="' + className + '">' + paths + '</svg>';
    return holder.firstElementChild;
  }

  // Django protects POST/DELETE requests with a CSRF token kept in a cookie.
  // This reads that cookie so api() can send it back with every request.
  function getCookie(name) {
    const row = document.cookie.split('; ').find((r) => r.startsWith(name + '='));
    return row ? decodeURIComponent(row.split('=')[1]) : '';
  }

  // api(url, options) calls one of OUR Django REST Framework endpoints and
  // returns the JSON answer. If the server replies with an error, it throws an
  // Error whose message comes from the "detail" field our views send back.
  async function api(url, options = {}) {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
        ...(options.headers || {}),
      },
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || 'Something went wrong. Please try again.');
    }
    // A successful DELETE answers "204 No Content": there is no JSON to read.
    return response.status === 204 ? null : response.json();
  }

  return { el, svg, getCookie, api };
})();