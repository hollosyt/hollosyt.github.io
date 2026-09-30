/* TeamKid Williamston · Jelly Mascots — small, dependency-free behaviours. */
(function () {
  "use strict";

  var root = document.documentElement;
  var reduced = matchMedia("(prefers-reduced-motion: reduce)");

  /* ---- theme (the <head> script applies a saved choice before paint) ---- */
  try {
    var saved = localStorage.getItem("tk-theme");
    if (saved === "light" || saved === "dark") root.setAttribute("data-theme", saved);
  } catch (e) {}

  document.addEventListener("click", function (e) {
    if (!e.target.closest("[data-theme-toggle]")) return;
    var isDark = root.getAttribute("data-theme") === "dark" ||
      (!root.hasAttribute("data-theme") && matchMedia("(prefers-color-scheme: dark)").matches);
    var next = isDark ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("tk-theme", next); } catch (err) {}
  });

  /* ---- sticky header shadow ------------------------------------------ */
  var header = document.querySelector(".site-header");
  if (header) {
    var onScroll = function () { header.classList.toggle("is-stuck", window.scrollY > 40); };
    onScroll();
    addEventListener("scroll", onScroll, { passive: true });
  }

  /* ---- mobile nav ------------------------------------------------------ */
  var burger = document.querySelector("[data-burger]");
  var nav = document.querySelector("[data-nav]");
  if (burger && nav) {
    var setOpen = function (open) {
      nav.classList.toggle("is-open", open);
      burger.setAttribute("aria-expanded", String(open));
    };
    burger.addEventListener("click", function () { setOpen(!nav.classList.contains("is-open")); });
    nav.addEventListener("click", function (e) { if (e.target.closest("a")) setOpen(false); });
    addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("is-open")) { setOpen(false); burger.focus(); }
    });
    addEventListener("resize", function () { if (innerWidth > 960) setOpen(false); }, { passive: true });
  }

  /* ---- reveal: content is always visible; it gets a jelly pop on arrival */
  var reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && !reduced.matches) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        el.style.setProperty("--i", el.dataset.delay || 0);
        el.classList.add("is-in");
        io.unobserve(el);
      });
    }, { rootMargin: "0px 0px -6% 0px", threshold: 0.06 });
    reveals.forEach(function (el) {
      // only pop things that start below the fold, so nothing on screen at load jumps
      if (el.getBoundingClientRect().top > innerHeight) io.observe(el);
    });
  }

  /* ---- role filters -------------------------------------------------- */
  var filterBar = document.querySelector("[data-filters]");
  if (filterBar) {
    var roles = Array.prototype.slice.call(document.querySelectorAll("[data-tags]"));
    var count = document.querySelector("[data-role-count]");
    filterBar.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-filter]");
      if (!btn) return;
      filterBar.querySelectorAll("[data-filter]").forEach(function (b) {
        b.setAttribute("aria-pressed", String(b === btn));
      });
      var key = btn.dataset.filter;
      var shown = 0;
      roles.forEach(function (card) {
        var match = key === "all" || card.dataset.tags.split(" ").indexOf(key) > -1;
        card.hidden = !match;
        if (match) {
          shown++;
          if (!reduced.matches) {
            card.classList.remove("is-in");
            void card.offsetWidth;
            card.style.setProperty("--i", shown - 1);
            card.classList.add("reveal", "is-in");
          }
        }
      });
      if (count) count.textContent = shown + " roles";
    });
  }

  /* ---- covenant tabs ------------------------------------------------- */
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
      var next = { ArrowRight: i + 1, ArrowDown: i + 1, ArrowLeft: i - 1, ArrowUp: i - 1, Home: 0, End: tabs.length - 1 }[e.key];
      if (next === undefined) return;
      e.preventDefault();
      var target = tabs[(next + tabs.length) % tabs.length];
      target.focus();
      select(target);
    });
  });

  /* ---- contact form: no backend, hand off to the mail app ------------ */
  var form = document.querySelector("[data-mail-form]");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var email = form.querySelector('[name="email"]');
      if (email && !email.checkValidity()) { email.reportValidity(); return; }
      var d = new FormData(form);
      var name = String(d.get("name") || "").trim();
      var from = String(d.get("email") || "").trim();
      var message = String(d.get("message") || "").trim();
      var body = message + "\n\n— " + (name || "a visitor") + (from ? " (" + from + ")" : "");
      location.href = "mailto:teamkidwilliamston@gmail.com" +
        "?subject=" + encodeURIComponent("Hello from the TeamKid website") +
        "&body=" + encodeURIComponent(body);
      var note = form.querySelector("[data-form-note]");
      if (note) note.hidden = false;
    });
  }

  /* ---- mascots: eyes follow the pointer; a click makes them squish --- */
  var mascots = Array.prototype.slice.call(document.querySelectorAll(".mascot"));
  if (mascots.length) {
    var px = null, py = null, raf = 0;
    var look = function () {
      raf = 0;
      mascots.forEach(function (m) {
        var eyes = m.querySelector(".m-look");
        if (!eyes) return;
        if (px === null) { eyes.removeAttribute("transform"); return; }
        var r = m.getBoundingClientRect();
        if (!r.width || r.bottom < 0 || r.top > innerHeight) return;
        var c = (m.getAttribute("data-eyes") || "60 41").split(" ");
        var ex = r.left + (c[0] / 120) * r.width;
        var ey = r.top + (c[1] / 160) * r.height;
        var dx = px - ex, dy = py - ey;
        var dist = Math.sqrt(dx * dx + dy * dy) || 1;
        var k = Math.min(dist / 160, 1) * 2.6 / dist;   // up to 2.6 units inside the head
        eyes.setAttribute("transform", "translate(" + (dx * k).toFixed(2) + " " + (dy * k * .8).toFixed(2) + ")");
      });
    };
    var queue = function () { if (!raf) raf = requestAnimationFrame(look); };
    addEventListener("pointermove", function (e) {
      if (e.pointerType === "touch") return;
      px = e.clientX; py = e.clientY; queue();
    }, { passive: true });
    document.documentElement.addEventListener("pointerleave", function () { px = py = null; queue(); });
    addEventListener("scroll", function () { if (px !== null) queue(); }, { passive: true });

    mascots.forEach(function (m) {
      m.addEventListener("click", function () {
        if (reduced.matches) return;
        m.classList.remove("is-squish");
        void m.getBoundingClientRect();
        m.classList.add("is-squish");
      });
      m.addEventListener("animationend", function (e) {
        if (e.animationName === "squish") m.classList.remove("is-squish");
      });
    });
  }

  /* ---- footer year --------------------------------------------------- */
  document.querySelectorAll("[data-year]").forEach(function (el) {
    el.textContent = String(new Date().getFullYear());
  });
})();
