/* =====================================================================
 * File: static/js/common.js
 * Purpose: Small bits of JavaScript used on every page (base.html loads
 *          this file). Everything still works without it - this only
 *          makes the pages nicer.
 * Contains:
 *   1. Tag input: turns the trip form's "Interests" text box into
 *      clickable tag chips with quick-pick suggestions.
 *      - Press Enter or comma to add a tag
 *      - Backspace on an empty box removes the last tag
 *      - Click the x on a chip to remove it
 *      - The real (hidden) box keeps the value "Food, Museums, Hiking",
 *        which is what Django receives when the form is saved
 *   2. User menu: closes the navbar menu when you click outside it or
 *      press Escape.
 * ===================================================================== */

(function () {
  "use strict";

  /* ---------------------------------------------------------------
   * 1. Tag input
   * Expected HTML (see templates/trips/trip_form.html):
   *   <div data-tag-input data-suggestions="Food,Culture,...">
   *     ... <input type="text" name="interests"> ...
   *   </div>
   * --------------------------------------------------------------- */
  var MAX_TAGS = 15;      // same limits as Trip.MAX_INTERESTS / MAX_INTEREST_LENGTH
  var MAX_LENGTH = 40;

  function initTagInput(root) {
    var original = root.querySelector('input[type="text"]');
    if (!original || original.dataset.tagReady) return;
    original.dataset.tagReady = "1";

    var tags = [];
    var suggestions = (root.dataset.suggestions || "")
      .split(",")
      .map(function (s) { return s.trim(); })
      .filter(Boolean);

    // Start from whatever the form already contains (e.g. when editing).
    original.value.split(",").forEach(function (part) { addTag(part, true); });

    // The visible box takes over the id so the <label> still works.
    var box = document.createElement("div");
    box.className =
      "form-input flex flex-wrap items-center gap-1.5 focus-within:border-brand-500 focus-within:ring-2 focus-within:ring-brand-100";

    var typing = document.createElement("input");
    typing.type = "text";
    typing.id = original.id;
    typing.placeholder = tags.length ? "" : "Add an interest…";
    typing.maxLength = MAX_LENGTH + 1;
    typing.autocomplete = "off";
    typing.className =
      "min-w-[8rem] flex-1 border-0 bg-transparent p-0 text-sm text-slate-900 focus:outline-none focus:ring-0";

    original.removeAttribute("id");
    original.type = "hidden";
    original.parentNode.insertBefore(box, original);
    box.appendChild(typing);

    var suggestionRow = document.createElement("div");
    suggestionRow.className = "mt-2 flex flex-wrap items-center gap-1.5";
    box.insertAdjacentElement("afterend", suggestionRow);

    function norm(s) { return s.trim().replace(/\s+/g, " "); }

    function has(tag) {
      return tags.some(function (t) { return t.toLowerCase() === tag.toLowerCase(); });
    }

    function addTag(raw, silent) {
      var tag = norm(raw);
      if (!tag || has(tag) || tags.length >= MAX_TAGS) return;
      tags.push(tag.slice(0, MAX_LENGTH));
      if (!silent) render();
    }

    function removeTag(tag) {
      tags = tags.filter(function (t) { return t !== tag; });
      render();
    }

    function render() {
      // Remove old chips, keep the typing box.
      Array.prototype.slice.call(box.querySelectorAll("[data-chip]")).forEach(function (el) {
        el.remove();
      });

      tags.forEach(function (tag) {
        var chip = document.createElement("span");
        chip.setAttribute("data-chip", "");
        chip.className = "tag inline-flex items-center gap-1";
        chip.appendChild(document.createTextNode(tag));

        var x = document.createElement("button");
        x.type = "button";
        x.setAttribute("aria-label", "Remove " + tag);
        x.className = "text-slate-400 hover:text-slate-700 leading-none";
        x.textContent = "×";
        x.addEventListener("click", function () { removeTag(tag); typing.focus(); });
        chip.appendChild(x);

        box.insertBefore(chip, typing);
      });

      original.value = tags.join(", ");
      typing.placeholder = tags.length ? "" : "Add an interest…";
      renderSuggestions();
    }

    function renderSuggestions() {
      suggestionRow.textContent = "";
      var remaining = suggestions.filter(function (s) { return !has(s); });
      if (!remaining.length) return;

      var label = document.createElement("span");
      label.className = "text-xs text-slate-500";
      label.textContent = "Quick add:";
      suggestionRow.appendChild(label);

      remaining.forEach(function (s) {
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className =
          "rounded-full border border-slate-200 bg-white px-2.5 py-0.5 text-xs text-slate-600 hover:border-brand-300 hover:text-brand-700";
        btn.textContent = "+ " + s;
        btn.addEventListener("click", function () { addTag(s); typing.focus(); });
        suggestionRow.appendChild(btn);
      });
    }

    function commitTyping() {
      if (typing.value.trim()) addTag(typing.value);
      typing.value = "";
    }

    typing.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === ",") {
        e.preventDefault();            // Enter must not submit the whole form
        commitTyping();
      } else if (e.key === "Backspace" && !typing.value && tags.length) {
        removeTag(tags[tags.length - 1]);
      }
    });

    // Pasting "Food, Museums, Hiking" adds three tags.
    typing.addEventListener("paste", function (e) {
      var text = (e.clipboardData || window.clipboardData).getData("text");
      if (text.indexOf(",") === -1) return;
      e.preventDefault();
      text.split(",").forEach(function (part) { addTag(part); });
    });

    typing.addEventListener("blur", commitTyping);

    // Safety net: anything still typed is added when the form is sent.
    var form = original.closest("form");
    if (form) form.addEventListener("submit", commitTyping);

    // Clicking the grey area focuses the typing box.
    box.addEventListener("click", function (e) { if (e.target === box) typing.focus(); });

    render();
  }

  /* ---------------------------------------------------------------
   * 2. User menu (the <details id="user-menu"> in the navbar)
   * --------------------------------------------------------------- */
  function initUserMenu() {
    var menu = document.getElementById("user-menu");
    if (!menu) return;

    document.addEventListener("click", function (e) {
      if (menu.open && !menu.contains(e.target)) menu.open = false;
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && menu.open) {
        menu.open = false;
        var summary = menu.querySelector("summary");
        if (summary) summary.focus();
      }
    });
  }

  function init() {
    document.querySelectorAll("[data-tag-input]").forEach(initTagInput);
    initUserMenu();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();