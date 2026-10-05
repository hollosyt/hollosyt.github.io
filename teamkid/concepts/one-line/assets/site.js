/* TeamKid Bible Club, One Line: small, dependency-free behaviours. */
(function () {
  "use strict";

  var root = document.documentElement;
  var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

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
      if (e.key === "Escape" && nav.classList.contains("is-open")) {
        setOpen(false);
        burger.focus();
      }
    });
    addEventListener("resize", function () {
      if (window.innerWidth > 860 && nav.classList.contains("is-open")) setOpen(false);
    });
  }

  /* ---- the line: never thinner than the pen weight, at any size -------- */
  var arts = Array.prototype.slice.call(document.querySelectorAll("svg.art"));
  var fit = function () {
    arts.forEach(function (svg) {
      var vb = svg.viewBox && svg.viewBox.baseVal;
      var w = svg.getBoundingClientRect().width;
      var h = svg.getBoundingClientRect().height;
      if (!vb || !w || !vb.width) return;
      var slice = (svg.getAttribute("preserveAspectRatio") || "").indexOf("slice") > -1;
      var scale = slice ? Math.max(w / vb.width, h / vb.height) : Math.min(w / vb.width, h / vb.height);
      var px = parseFloat(svg.getAttribute("data-pen") || "2.4");
      if (w < 480) px = px * 0.86;
      svg.style.setProperty("--sw", (px / scale).toFixed(2));
      var bw = parseFloat(svg.getAttribute("data-brush") || "0");
      if (bw) {
        var pmin = Math.max(0, px - bw * scale);
        svg.style.setProperty("--pmin", pmin.toFixed(2));
        svg.style.setProperty("--mw", (bw * 1.8 + 2 * pmin / scale + 1.5).toFixed(1));
      }
    });
  };
  fit();
  addEventListener("resize", fit, { passive: true });

  /* ---- the line draws itself once, as it comes into view ------------- */
  var draws = Array.prototype.slice.call(document.querySelectorAll(".draw, .hl--swipe"));
  var light = function (el) { el.classList.add(el.classList.contains("hl--swipe") ? "is-lit" : "is-drawn"); };
  if (root.classList.contains("js-draw")) {
    if (reduce || !("IntersectionObserver" in window)) {
      root.classList.remove("js-draw");
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          light(entry.target);
          io.unobserve(entry.target);
        });
      }, { rootMargin: "0px 0px -12% 0px", threshold: 0.15 });
      draws.forEach(function (el) { io.observe(el); });
    }
  }
  window.__oneLineReady = true;

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
        if (match) shown++;
      });
      if (count) count.textContent = shown + " roles";
    });
  }

  /* ---- tabs (covenants) --------------------------------------------- */
  document.querySelectorAll("[data-tabs]").forEach(function (group) {
    var tabs = Array.prototype.slice.call(group.querySelectorAll('[role="tab"]'));
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
      var tab = e.target.closest('[role="tab"]');
      if (tab) select(tab);
    });
    group.addEventListener("keydown", function (e) {
      var i = tabs.indexOf(document.activeElement);
      if (i < 0) return;
      var next = null;
      if (e.key === "ArrowRight") next = (i + 1) % tabs.length;
      else if (e.key === "ArrowLeft") next = (i - 1 + tabs.length) % tabs.length;
      else if (e.key === "Home") next = 0;
      else if (e.key === "End") next = tabs.length - 1;
      if (next === null) return;
      e.preventDefault();
      tabs[next].focus();
      select(tabs[next]);
    });
  });

  /* ---- contact form (no backend: hand off to the mail app) ----------- */
  var form = document.querySelector("[data-mail-form]");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var email = form.querySelector('[name="email"]');
      if (email && !email.checkValidity()) {
        email.reportValidity();
        return;
      }
      var d = new FormData(form);
      var name = String(d.get("name") || "").trim();
      var from = String(d.get("email") || "").trim();
      var message = String(d.get("message") || "").trim();
      var body = message + "\n\n" + (name || "") + (from ? " (" + from + ")" : "");
      location.href = "mailto:teamkidwilliamston@gmail.com" +
        "?subject=" + encodeURIComponent("TeamKid Bible Club") +
        "&body=" + encodeURIComponent(body.trim());
      var note = form.querySelector("[data-form-note]");
      if (note) note.hidden = false;
    });
  }
})();
