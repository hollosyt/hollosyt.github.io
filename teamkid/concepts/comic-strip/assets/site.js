/* TeamKid Williamston — Comic Strip concept. Small, dependency-free behaviours. */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---- sticky header ------------------------------------------------ */
  var header = document.querySelector(".site-header");
  if (header) {
    var onScroll = function () { header.classList.toggle("is-stuck", window.scrollY > 8); };
    onScroll();
    addEventListener("scroll", onScroll, { passive: true });
  }

  /* ---- mobile nav --------------------------------------------------- */
  var burger = document.querySelector("[data-burger]");
  var nav = document.querySelector("[data-nav]");
  if (burger && nav) {
    var setOpen = function (open) {
      nav.classList.toggle("is-open", open);
      burger.setAttribute("aria-expanded", String(open));
    };
    burger.addEventListener("click", function () {
      setOpen(burger.getAttribute("aria-expanded") !== "true");
    });
    nav.addEventListener("click", function (e) {
      if (e.target.closest("a")) setOpen(false);
    });
    addEventListener("keydown", function (e) {
      if (e.key === "Escape" && burger.getAttribute("aria-expanded") === "true") {
        setOpen(false);
        burger.focus();
      }
    });
    // Leaving mobile layout with the menu open: reset it.
    if (window.matchMedia) {
      var wide = matchMedia("(min-width: 961px)");
      var reset = function () { if (wide.matches) setOpen(false); };
      if (wide.addEventListener) wide.addEventListener("change", reset);
    }
  }

  /* ---- panels settle in on scroll ------------------------------------ */
  // Everything is visible at rest. Only panels that start below the fold get
  // a lifted, tipped pose (`is-pending`) and drop into place when they arrive.
  var reveals = Array.prototype.slice.call(document.querySelectorAll(".reveal"));
  if (!reduceMotion && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        var siblings = el.parentElement ? Array.prototype.indexOf.call(el.parentElement.children, el) : 0;
        setTimeout(function () { el.classList.remove("is-pending"); }, Math.min(siblings, 4) * 70);
        io.unobserve(el);
      });
    }, { rootMargin: "0px 0px -6% 0px", threshold: 0.06 });
    var fold = window.innerHeight;
    reveals.forEach(function (el) {
      if (el.getBoundingClientRect().top > fold) {
        el.classList.add("is-pending");
        io.observe(el);
      }
    });
  }

  /* ---- role filters ------------------------------------------------- */
  var filterBar = document.querySelector("[data-filters]");
  if (filterBar) {
    var roles = Array.prototype.slice.call(document.querySelectorAll("[data-tags]"));
    var count = document.querySelector("[data-role-count]");
    filterBar.addEventListener("click", function (e) {
      var btn = e.target.closest(".filter");
      if (!btn) return;
      filterBar.querySelectorAll(".filter").forEach(function (b) {
        b.setAttribute("aria-pressed", String(b === btn));
      });
      var key = btn.getAttribute("data-filter");
      var shown = 0;
      roles.forEach(function (card) {
        var match = key === "all" || card.getAttribute("data-tags").split(" ").indexOf(key) > -1;
        card.hidden = !match;
        card.classList.remove("is-pending", "is-popping");
        if (match) {
          shown++;
          if (!reduceMotion) {
            void card.offsetWidth; // restart the pop
            card.classList.add("is-popping");
          }
        }
      });
      if (count) count.textContent = shown + " roles";
    });
  }

  /* ---- tabs (covenants) --------------------------------------------- */
  document.querySelectorAll("[data-tabs]").forEach(function (group) {
    var tabs = Array.prototype.slice.call(group.querySelectorAll("[role='tab']"));
    var select = function (tab) {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.setAttribute("aria-selected", String(on));
        t.tabIndex = on ? 0 : -1;
        var panel = document.getElementById(t.getAttribute("aria-controls"));
        if (panel) panel.hidden = !on;
      });
    };
    group.addEventListener("click", function (e) {
      var tab = e.target.closest("[role='tab']");
      if (tab) select(tab);
    });
    group.addEventListener("keydown", function (e) {
      var i = tabs.indexOf(document.activeElement);
      if (i < 0) return;
      var next = -1;
      if (e.key === "ArrowRight") next = (i + 1) % tabs.length;
      else if (e.key === "ArrowLeft") next = (i - 1 + tabs.length) % tabs.length;
      else if (e.key === "Home") next = 0;
      else if (e.key === "End") next = tabs.length - 1;
      if (next < 0) return;
      e.preventDefault();
      tabs[next].focus();
      select(tabs[next]);
    });
  });

  /* ---- contact form (no backend: hand off to the mail app) ------------ */
  var form = document.querySelector("[data-mail-form]");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var d = new FormData(form);
      var name = String(d.get("name") || "").trim();
      var email = String(d.get("email") || "").trim();
      var message = String(d.get("message") || "").trim();
      var body = message + "\n\n— " + (name || "a visitor") + (email ? " (" + email + ")" : "");
      window.location.href = "mailto:teamkidwilliamston@gmail.com" +
        "?subject=" + encodeURIComponent("Hello from the TeamKid website") +
        "&body=" + encodeURIComponent(body);
      var note = form.querySelector("[data-form-note]");
      if (note) note.hidden = false;
    });
  }

  /* ---- footer year --------------------------------------------------- */
  document.querySelectorAll("[data-year]").forEach(function (el) {
    el.textContent = String(new Date().getFullYear());
  });
})();
