/* Music workbench - optional enhancements for the static pages built
   from sites/music/content/catalog.toml (design/music.md, step 5).
   Replaces the prototype's app.js; the pages work fully without it.

   What it adds:
   - search and filter the piece index (remembered for this browser tab)
   - the "/" key jumps to the search box
   - welcome page: this visitor's 3 most recently opened pieces as tiles
     (the section stays hidden until there is at least one)
   - per-piece status and checklist ticks, saved in this browser

   Rules, for safety and easy review:
   - never builds HTML from strings: only textContent, the `hidden`
     property, attributes, and moving existing elements - no innerHTML,
     no eval. All visible text comes from the server-built page, in the
     page's language.
   - anything read back from storage is checked (types, known piece ids,
     known statuses) before use; anything else is ignored
   - storage failures (private windows, blocked storage) are silent: the
     page just doesn't remember
   - plain ES2017, so tools/dev/pre-build-check.sh can syntax-check it
     with a Python parser (no Node toolchain in this project) */

(function () {
  "use strict";

  var PREFIX = "music-workbench:";
  var RECENT_MAX = 3;

  // --- storage ---------------------------------------------------------

  function load(store, key, fallback, isValid) {
    try {
      var value = JSON.parse(store.getItem(PREFIX + key));
      return isValid(value) ? value : fallback;
    } catch (err) {
      return fallback;
    }
  }

  function save(store, key, value) {
    try {
      store.setItem(PREFIX + key, JSON.stringify(value));
    } catch (err) {
      // Storage unavailable: carry on without remembering.
    }
  }

  function isStringArray(value) {
    return Array.isArray(value) && value.every(function (x) { return typeof x === "string"; });
  }

  function isPlainObject(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
  }

  function has(obj, key) {
    return Object.prototype.hasOwnProperty.call(obj, key);
  }

  // --- what this page contains -----------------------------------------

  var pieceLinks = Array.from(document.querySelectorAll("#piece-list [data-piece]"));
  var knownIds = new Set(pieceLinks.map(function (a) { return a.dataset.piece; }));
  var currentLink = document.querySelector("#piece-list [aria-current='page']");
  var currentId = currentLink ? currentLink.dataset.piece : null;

  var statusLabels = {};
  try {
    var parsed = JSON.parse(document.getElementById("status-labels").textContent);
    if (isPlainObject(parsed)) statusLabels = parsed;
  } catch (err) {
    // Without labels, stored statuses simply aren't shown in the sidebar.
  }

  function isKnownStatus(value) {
    return typeof value === "string" && has(statusLabels, value);
  }

  Array.from(document.querySelectorAll("[data-enhanced]")).forEach(function (el) {
    el.hidden = false;
  });

  // --- search and filters -------------------------------------------------

  var search = document.getElementById("search");
  var chips = Array.from(document.querySelectorAll(".filter-chip"));
  var resultCount = document.getElementById("result-count");
  var noMatches = document.getElementById("no-matches");

  function applyFilters() {
    var term = search.value.trim().toLowerCase();
    var active = {};
    chips.forEach(function (chip) {
      if (chip.getAttribute("aria-pressed") === "true") {
        (active[chip.dataset.group] = active[chip.dataset.group] || []).push(chip.dataset.filter);
      }
    });
    var groups = Object.keys(active);
    var shown = 0;
    pieceLinks.forEach(function (link) {
      // Any chip within a group may match; every group with a chip must.
      var matches =
        (!term || link.dataset.search.indexOf(term) !== -1) &&
        groups.every(function (group) {
          var tags = (link.dataset[group] || "").split(" ");
          return active[group].some(function (key) { return tags.indexOf(key) !== -1; });
        });
      link.hidden = !matches;
      if (matches) shown += 1;
    });
    resultCount.textContent = String(shown);
    noMatches.hidden = shown > 0;
    // Remembered for this tab only, so the index keeps its filters while
    // moving between pieces (each piece is a separate page).
    save(sessionStorage, "view", { term: search.value, active: active });
  }

  var view = load(sessionStorage, "view", {}, isPlainObject);
  if (typeof view.term === "string") search.value = view.term;
  if (isPlainObject(view.active)) {
    chips.forEach(function (chip) {
      var keys = view.active[chip.dataset.group];
      var on = isStringArray(keys) && keys.indexOf(chip.dataset.filter) !== -1;
      chip.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }

  search.addEventListener("input", applyFilters);
  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      var on = chip.getAttribute("aria-pressed") !== "true";
      chip.setAttribute("aria-pressed", on ? "true" : "false");
      applyFilters();
    });
  });
  document.getElementById("clear-filters").addEventListener("click", function () {
    chips.forEach(function (chip) { chip.setAttribute("aria-pressed", "false"); });
    applyFilters();
  });
  document.addEventListener("keydown", function (event) {
    var tag = document.activeElement ? document.activeElement.tagName : "";
    if (event.key === "/" && !event.ctrlKey && !event.metaKey && !event.altKey &&
        ["INPUT", "TEXTAREA", "SELECT"].indexOf(tag) === -1) {
      event.preventDefault();
      search.focus();
    }
  });
  applyFilters();

  // --- recently opened (welcome page tiles) ------------------------------

  var recent = load(localStorage, "recent", [], isStringArray).filter(function (id) {
    return knownIds.has(id);
  });
  if (currentId) {
    recent = [currentId].concat(recent.filter(function (id) { return id !== currentId; }));
    recent = recent.slice(0, RECENT_MAX);
    save(localStorage, "recent", recent);
  }

  var tilesSection = document.getElementById("recent-tiles");
  if (tilesSection && recent.length) {
    var grid = document.getElementById("welcome-grid");
    recent.forEach(function (id, index) {
      var tile = grid.querySelector("[data-tile='" + CSS.escape(id) + "']");
      if (!tile) return;
      tile.querySelector("[data-tile-no]").textContent = String(index + 1).padStart(2, "0");
      tile.hidden = false;
      grid.appendChild(tile); // appending in recency order = newest first
    });
    tilesSection.hidden = false;
  }

  // --- status ------------------------------------------------------------------

  var statuses = load(localStorage, "status", {}, isPlainObject);

  Array.from(document.querySelectorAll("[data-status-for]")).forEach(function (el) {
    var saved = statuses[el.dataset.statusFor];
    if (isKnownStatus(saved)) el.textContent = statusLabels[saved];
  });

  var select = document.getElementById("status-select");
  if (select) {
    var pieceId = select.dataset.piece;
    var statusTag = document.getElementById("status-tag");
    var savedNote = document.getElementById("saved-note");
    var miniStatus = document.querySelector("[data-status-for='" + CSS.escape(pieceId) + "']");
    if (isKnownStatus(statuses[pieceId])) {
      select.value = statuses[pieceId];
      statusTag.textContent = statusLabels[statuses[pieceId]];
    }
    select.addEventListener("change", function () {
      statuses[pieceId] = select.value;
      save(localStorage, "status", statuses);
      var text = select.options[select.selectedIndex].textContent;
      statusTag.textContent = text;
      if (miniStatus) miniStatus.textContent = text;
      savedNote.textContent = savedNote.dataset.text;
    });
  }

  // --- checklist ------------------------------------------------------------

  var checklist = document.querySelector(".check-list[data-piece]");
  if (checklist) {
    var listId = checklist.dataset.piece;
    var checks = load(localStorage, "checks", {}, isPlainObject);
    var boxes = Array.from(checklist.querySelectorAll("input[data-check]"));
    var done = Array.isArray(checks[listId]) ? checks[listId] : [];
    boxes.forEach(function (box) {
      box.checked = done.indexOf(Number(box.dataset.check)) !== -1;
    });
    checklist.addEventListener("change", function () {
      checks[listId] = boxes
        .filter(function (box) { return box.checked; })
        .map(function (box) { return Number(box.dataset.check); });
      save(localStorage, "checks", checks);
    });
  }
})();
