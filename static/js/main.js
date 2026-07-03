// TDx front-end JS — vanilla, no third-party dependencies (keeps the CSP
// script-src locked to 'self' and avoids supply-chain risk from CDNs).
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    // Mobile nav toggle
    var toggle = document.querySelector(".nav-toggle");
    if (toggle) {
      toggle.addEventListener("click", function () {
        document.body.classList.toggle("nav-open");
      });
    }

    // Language dropdown
    var langBtn = document.querySelector(".lang-btn");
    var langMenu = document.querySelector(".lang-menu");
    if (langBtn && langMenu) {
      langBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        langMenu.classList.toggle("open");
      });
      document.addEventListener("click", function () {
        langMenu.classList.remove("open");
      });
    }

    // Gallery lightbox
    var lightbox = document.querySelector(".lightbox");
    if (lightbox) {
      var lightboxImg = lightbox.querySelector("img");
      document.querySelectorAll("[data-lightbox-src]").forEach(function (el) {
        el.addEventListener("click", function () {
          lightboxImg.src = el.getAttribute("data-lightbox-src");
          lightboxImg.alt = el.getAttribute("data-lightbox-alt") || "";
          lightbox.classList.add("open");
        });
      });
      lightbox.addEventListener("click", function (e) {
        if (e.target === lightbox || e.target.classList.contains("lightbox-close")) {
          lightbox.classList.remove("open");
          lightboxImg.src = "";
        }
      });
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") {
          lightbox.classList.remove("open");
          lightboxImg.src = "";
        }
      });
    }

    // Dashboard tabs (used on multilingual content forms)
    document.querySelectorAll(".tab-row").forEach(function (row) {
      var buttons = row.querySelectorAll(".tab-btn");
      buttons.forEach(function (btn) {
        btn.addEventListener("click", function () {
          var target = btn.getAttribute("data-tab-target");
          var panelGroup = document.querySelector(btn.getAttribute("data-tab-group"));
          buttons.forEach(function (b) { b.classList.remove("active"); });
          btn.classList.add("active");
          if (panelGroup) {
            panelGroup.querySelectorAll(".tab-panel").forEach(function (p) {
              p.classList.toggle("active", p.id === target);
            });
          }
        });
      });
    });

    // Auto-dismiss alerts
    document.querySelectorAll(".alert[data-autohide]").forEach(function (el) {
      setTimeout(function () { el.style.display = "none"; }, 6000);
    });

    // Confirm destructive actions client-side as a UX nicety
    // (server-side CSRF + POST-only requirement is the actual security control).
    document.querySelectorAll("[data-confirm]").forEach(function (el) {
      el.addEventListener("click", function (e) {
        if (!window.confirm(el.getAttribute("data-confirm"))) {
          e.preventDefault();
        }
      });
    });

    // Animated stat counters
    var statEls = document.querySelectorAll(".stat-value[data-count]");
    if (statEls.length && "IntersectionObserver" in window) {
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var el = entry.target;
          var raw = el.getAttribute("data-count");
          var match = raw.match(/^(\d+)(.*)$/);
          if (!match) return;
          var target = parseInt(match[1], 10);
          var suffix = match[2] || "";
          var current = 0;
          var step = Math.max(1, Math.round(target / 30));
          var timer = setInterval(function () {
            current += step;
            if (current >= target) {
              current = target;
              clearInterval(timer);
            }
            el.textContent = current + suffix;
          }, 30);
          observer.unobserve(el);
        });
      }, { threshold: 0.4 });
      statEls.forEach(function (el) { observer.observe(el); });
    }
  });
})();
