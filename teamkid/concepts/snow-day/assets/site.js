/* TeamKid Williamston · Concept 5 · Snow Day — small, dependency-free behaviours. */
(function () {
  "use strict";

  var root = document.documentElement;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  var prefersDark = window.matchMedia("(prefers-color-scheme: dark)");
  var onChange = function (mq, fn) {
    if (mq.addEventListener) mq.addEventListener("change", fn); else if (mq.addListener) mq.addListener(fn);
  };

  /* ---- theme -------------------------------------------------------- */
  try {
    var saved = localStorage.getItem("tk-theme");
    if (saved === "light" || saved === "dark") root.setAttribute("data-theme", saved);
  } catch (e) {}

  document.addEventListener("click", function (e) {
    if (!e.target.closest("[data-theme-toggle]")) return;
    var isDark = root.getAttribute("data-theme") === "dark" ||
      (!root.hasAttribute("data-theme") && prefersDark.matches);
    var next = isDark ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("tk-theme", next); } catch (err) {}
  });

  /* ---- sticky header ------------------------------------------------ */
  var header = document.querySelector(".site-header");
  if (header) {
    var stuck = function () { header.classList.toggle("is-stuck", window.scrollY > 8); };
    stuck();
    addEventListener("scroll", stuck, { passive: true });
  }

  /* ---- mobile nav --------------------------------------------------- */
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
    document.addEventListener("click", function (e) {
      if (nav.classList.contains("is-open") && !e.target.closest("[data-nav], [data-burger]")) setOpen(false);
    });
  }

  /* ---- scroll reveal (only below-the-fold items ever start hidden) --- */
  var reveals = Array.prototype.slice.call(document.querySelectorAll(".reveal"));
  if ("IntersectionObserver" in window && !reduce.matches && reveals.length) {
    var vh = window.innerHeight || 800;
    var pending = reveals.filter(function (el) { return el.getBoundingClientRect().top > vh * .92; });
    if (pending.length) {
      root.classList.add("sd-reveal");
      pending.forEach(function (el) { el.classList.add("is-pending"); });
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var el = entry.target;
          setTimeout(function () { el.classList.remove("is-pending"); }, Number(el.dataset.delay || 0) * 90);
          io.unobserve(el);
        });
      }, { rootMargin: "0px 0px -6% 0px", threshold: 0.05 });
      pending.forEach(function (el) { io.observe(el); });
      // Anything still waiting after a jump (anchor link, print, etc.) shows anyway.
      onChange(reduce, function () { pending.forEach(function (el) { el.classList.remove("is-pending"); }); });
      addEventListener("beforeprint", function () { pending.forEach(function (el) { el.classList.remove("is-pending"); }); });
    }
  }

  /* ---- role filters ------------------------------------------------- */
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
      var key = btn.getAttribute("data-filter");
      var shown = 0;
      roles.forEach(function (card) {
        var match = key === "all" || card.getAttribute("data-tags").split(" ").indexOf(key) > -1;
        card.hidden = !match;
        card.classList.remove("is-pending", "is-pop");
        if (match) {
          shown++;
          if (!reduce.matches) { void card.offsetWidth; card.classList.add("is-pop"); }
        }
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
      var next = { ArrowRight: i + 1, ArrowDown: i + 1, ArrowLeft: i - 1, ArrowUp: i - 1, Home: 0, End: tabs.length - 1 }[e.key];
      if (next === undefined) return;
      e.preventDefault();
      var target = tabs[(next + tabs.length) % tabs.length];
      target.focus();
      select(target);
    });
  });

  /* ---- contact form (no backend: hand off to the mail client) -------- */
  var form = document.querySelector("[data-mail-form]");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var emailField = form.querySelector('[name="email"]');
      if (emailField && !emailField.checkValidity()) { emailField.reportValidity(); emailField.focus(); return; }
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

  /* ---- gentle snowfall in the hero skies ------------------------------ */
  function Snowfall(canvas) {
    var ctx = canvas.getContext("2d");
    var flakes = [], w = 0, h = 0, raf = 0, last = 0, visible = true;
    if (!ctx) return;
    function make(anywhere) {
      return {
        x: Math.random() * w, y: anywhere ? Math.random() * h : -8,
        r: .9 + Math.random() * 2.6, v: 14 + Math.random() * 26,
        ph: Math.random() * 6.28, sw: .5 + Math.random() * 1.2, a: .55 + Math.random() * .45
      };
    }
    function size() {
      var r = canvas.getBoundingClientRect();
      var dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = r.width; h = r.height;
      canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      var n = Math.round(Math.min(110, w * h / 8500));
      while (flakes.length < n) flakes.push(make(true));
      flakes.length = n;
    }
    function frame(t) {
      var dt = Math.min(.05, (t - (last || t)) / 1000);
      last = t;
      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = "#fff";
      for (var i = 0; i < flakes.length; i++) {
        var p = flakes[i];
        p.y += p.v * (p.r / 2.4 + .4) * dt;
        p.ph += p.sw * dt;
        var x = p.x + Math.sin(p.ph) * 14;
        if (p.y > h + 6) { flakes[i] = make(false); continue; }
        ctx.globalAlpha = p.a;
        ctx.beginPath(); ctx.arc(x, p.y, p.r, 0, 6.2832); ctx.fill();
      }
      ctx.globalAlpha = 1;
      raf = requestAnimationFrame(frame);
    }
    function start() { if (!raf && visible && !reduce.matches && !document.hidden) { last = 0; raf = requestAnimationFrame(frame); } }
    function stop() { if (raf) cancelAnimationFrame(raf); raf = 0; }
    size();
    addEventListener("resize", function () { size(); }, { passive: true });
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (en) { visible = en[0].isIntersecting; visible ? start() : stop(); }).observe(canvas);
    }
    document.addEventListener("visibilitychange", function () { document.hidden ? stop() : start(); });
    onChange(reduce, function () { if (reduce.matches) { stop(); ctx.clearRect(0, 0, w, h); } else start(); });
    start();
  }
  document.querySelectorAll("[data-snowfall]").forEach(function (c) { Snowfall(c); });

  /* ---- snowball throw: click empty background ------------------------ */
  var NOT_BACKGROUND = "a, button, input, textarea, select, label, summary, details, form, [role='tab'], [role='button'], " +
    "[tabindex], [contenteditable], p, h1, h2, h3, h4, li, dt, dd, blockquote, figcaption, span, b, strong, em, " +
    ".site-header, [data-concept-ui]";
  var MAX_BALLS = 5;
  var layer = null, lctx = null, balls = [], bits = [], lraf = 0, lw = 0, lh = 0, llast = 0;

  function sizeLayer() {
    if (!layer) return;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    lw = window.innerWidth; lh = window.innerHeight;
    layer.width = Math.round(lw * dpr); layer.height = Math.round(lh * dpr);
    lctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  function ensureLayer() {
    if (layer) return true;
    layer = document.createElement("canvas");
    layer.className = "snowball-layer";
    layer.setAttribute("aria-hidden", "true");
    lctx = layer.getContext("2d");
    if (!lctx) { layer = null; return false; }
    document.body.appendChild(layer);
    sizeLayer();
    addEventListener("resize", sizeLayer, { passive: true });
    return true;
  }
  function drawBall(x, y, r) {
    var g = lctx.createRadialGradient(x - r * .35, y - r * .4, r * .1, x, y, r);
    g.addColorStop(0, "#ffffff"); g.addColorStop(.7, "#f1f8ff"); g.addColorStop(1, "#c8e2f7");
    lctx.fillStyle = g;
    lctx.strokeStyle = "rgba(14,39,72,.55)";
    lctx.lineWidth = 1.5;
    lctx.beginPath(); lctx.arc(x, y, r, 0, 6.2832); lctx.fill(); lctx.stroke();
  }
  function splat(x, y) {
    var n = 14 + Math.floor(Math.random() * 6);
    for (var i = 0; i < n; i++) {
      var ang = Math.random() * 6.2832, sp = 70 + Math.random() * 190;
      bits.push({ x: x, y: y, vx: Math.cos(ang) * sp, vy: Math.sin(ang) * sp - 90, r: 1.6 + Math.random() * 3.4, life: 0, max: .6 + Math.random() * .45 });
    }
    bits.push({ x: x, y: y, blob: true, life: 0, max: .9, r: 16 });
  }
  function tick(t) {
    var dt = Math.min(.05, (t - (llast || t)) / 1000);
    llast = t;
    lctx.clearRect(0, 0, lw, lh);
    for (var i = bits.length - 1; i >= 0; i--) {
      var b = bits[i];
      b.life += dt;
      var k = b.life / b.max;
      if (k >= 1) { bits.splice(i, 1); continue; }
      lctx.globalAlpha = 1 - k * k;
      if (b.blob) {
        lctx.fillStyle = "#ffffff"; lctx.strokeStyle = "rgba(46,110,180,.35)"; lctx.lineWidth = 1.2;
        var rr = b.r * (1 + k * .9);
        lctx.beginPath();
        for (var j = 0; j <= 10; j++) {
          var a = j / 10 * 6.2832, wob = rr * (.72 + .28 * Math.sin(a * 3 + 1.3));
          var px = b.x + Math.cos(a) * wob, py = b.y + Math.sin(a) * wob * .8;
          j ? lctx.lineTo(px, py) : lctx.moveTo(px, py);
        }
        lctx.closePath(); lctx.fill(); lctx.stroke();
      } else {
        b.vy += 520 * dt; b.vx *= .985;
        b.x += b.vx * dt; b.y += b.vy * dt;
        lctx.fillStyle = "#ffffff"; lctx.strokeStyle = "rgba(46,110,180,.5)"; lctx.lineWidth = 1;
        lctx.beginPath(); lctx.arc(b.x, b.y, b.r * (1 - k * .4), 0, 6.2832); lctx.fill(); lctx.stroke();
      }
    }
    lctx.globalAlpha = 1;
    for (var m = balls.length - 1; m >= 0; m--) {
      var s = balls[m];
      s.t += dt / s.dur;
      if (s.t >= 1) { splat(s.tx, s.ty); balls.splice(m, 1); continue; }
      var u = s.t, iu = 1 - u;
      var bx = iu * iu * s.sx + 2 * iu * u * s.cx + u * u * s.tx;
      var by = iu * iu * s.sy + 2 * iu * u * s.cy + u * u * s.ty;
      drawBall(bx, by, 17 - 8 * u);
    }
    if (balls.length || bits.length) lraf = requestAnimationFrame(tick);
    else { lraf = 0; llast = 0; }
  }
  function throwAt(tx, ty) {
    if (!ensureLayer()) return;
    var sx = Math.max(24, Math.min(lw - 24, tx + (Math.random() - .5) * 220));
    var sy = lh + 26;
    var dist = Math.hypot(tx - sx, ty - sy);
    balls.push({
      sx: sx, sy: sy, tx: tx, ty: ty,
      cx: (sx + tx) / 2 + (Math.random() - .5) * 60, cy: Math.min(sy, ty) - (70 + dist * .3),
      t: 0, dur: Math.max(.38, Math.min(.8, .3 + dist / 1600))
    });
    if (!lraf) lraf = requestAnimationFrame(tick);
  }
  document.addEventListener("click", function (e) {
    if (reduce.matches || e.button !== 0 || e.defaultPrevented) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    if (!(e.target instanceof Element) || e.target.closest(NOT_BACKGROUND)) return;
    var sel = window.getSelection && window.getSelection();
    if (sel && String(sel).length) return;
    if (balls.length >= MAX_BALLS) return;
    throwAt(e.clientX, e.clientY);
  });
  onChange(reduce, function () {
    if (reduce.matches && layer) { balls = []; bits = []; lctx.clearRect(0, 0, lw, lh); }
  });

  /* ---- the season hill: the sled slides down as you scroll ---------- */
  var hill = document.querySelector("[data-hill]");
  if (hill) {
    var narrow = window.matchMedia("(max-width: 759px)");
    var queued = false;
    var place = function () {
      queued = false;
      var r = hill.getBoundingClientRect();
      if (!narrow.matches && r.width) {
        hill.style.setProperty("--ang", (Math.atan2(280, r.width) * 180 / Math.PI).toFixed(2) + "deg");
      }
      if (reduce.matches) { hill.style.removeProperty("--p"); return; }
      var vh = window.innerHeight || 800;
      var p = (vh * .95 - (r.top + r.height * .5)) / (vh * .62);
      p = Math.max(0, Math.min(1, p));
      hill.style.setProperty("--p", (p * p * (3 - 2 * p)).toFixed(4));
    };
    var queue = function () { if (!queued) { queued = true; requestAnimationFrame(place); } };
    place();
    addEventListener("scroll", queue, { passive: true });
    addEventListener("resize", queue, { passive: true });
    onChange(reduce, queue);
    onChange(narrow, queue);
  }
})();
