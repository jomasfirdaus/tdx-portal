/*
 * Location Map module — initialises one Leaflet map per `.location-map`
 * element, using data-* attributes rendered by
 * templates/partials/location_map.html.
 *
 * Kept as an external file (no inline JS) so the site's strict
 * Content-Security-Policy (script-src 'self') stays intact. Tiles come from
 * OpenStreetMap — no API key required.
 */
(function () {
  "use strict";

  function escapeHtml(value) {
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(value || ""));
    return div.innerHTML;
  }

  function initMap(el) {
    var lat = parseFloat(el.dataset.lat);
    var lng = parseFloat(el.dataset.lng);
    if (isNaN(lat) || isNaN(lng)) return;

    var map = L.map(el, {
      center: [lat, lng],
      zoom: 16,
      scrollWheelZoom: false, // avoid hijacking page scroll, esp. on touchpads
      tap: true,
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors',
    }).addTo(map);

    // Re-enable scroll zoom only after the user deliberately interacts.
    map.on("click focus", function () { map.scrollWheelZoom.enable(); });
    map.on("blur", function () { map.scrollWheelZoom.disable(); });

    var name = escapeHtml(el.dataset.name);
    var address = escapeHtml(el.dataset.address);
    var directionsUrl = el.dataset.directionsUrl || "";
    var directionsLabel = escapeHtml(el.dataset.directionsLabel || "Get Directions");

    var popupHtml =
      '<div class="map-popup">' +
      "<strong>" + name + "</strong><br>" +
      address +
      (directionsUrl
        ? '<br><a href="' + escapeHtml(directionsUrl) + '" target="_blank" rel="noopener noreferrer">' + directionsLabel + " &rarr;</a>"
        : "") +
      "</div>";

    L.marker([lat, lng], { alt: name })
      .addTo(map)
      .bindPopup(popupHtml)
      .openPopup();

    // Keep the marker centred when the container is resized (responsive
    // layouts, orientation changes).
    var onResize = function () {
      map.invalidateSize();
      map.setView([lat, lng]);
    };
    if (typeof ResizeObserver !== "undefined") {
      new ResizeObserver(onResize).observe(el);
    } else {
      window.addEventListener("resize", onResize);
    }
  }

  function boot() {
    if (typeof L === "undefined") return; // Leaflet failed to load; info card still shows everything
    document.querySelectorAll(".location-map").forEach(initMap);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
