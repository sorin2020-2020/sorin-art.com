(function () {
  "use strict";

  // Current year in footer
  document.querySelectorAll("[data-year]").forEach(function (el) { el.textContent = new Date().getFullYear(); });

  // Remote (YouTube) thumbnails: hide gracefully when offline
  document.querySelectorAll("img[data-remote]").forEach(function (img) {
    function fail() { img.style.visibility = "hidden"; }
    if (img.complete && img.naturalWidth === 0) fail();
    img.addEventListener("error", fail);
    // maxresdefault is missing for some videos; YouTube then serves a 120px grey placeholder
    img.addEventListener("load", function () {
      if (img.naturalWidth <= 120 && /maxresdefault/.test(img.src)) img.src = img.src.replace("maxresdefault", "hqdefault");
    });
  });

  // Video: load the YouTube player only when asked
  document.querySelectorAll(".video-play").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var id = btn.getAttribute("data-video");
      var start = parseInt(btn.getAttribute("data-start") || "0", 10);
      var f = document.createElement("iframe");
      f.src = "https://www.youtube-nocookie.com/embed/" + id + "?autoplay=1&rel=0" + (start ? "&start=" + start : "");
      f.title = btn.getAttribute("aria-label").replace("Play video: ", "");
      f.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen";
      f.allowFullscreen = true;
      f.referrerPolicy = "strict-origin-when-cross-origin";
      btn.replaceWith(f);
      f.focus();
    });
  });

  // Lightbox
  var links = Array.prototype.slice.call(document.querySelectorAll("a[data-lightbox]"));
  if (!links.length || typeof HTMLDialogElement !== "function") return;

  var dlg = document.createElement("dialog");
  dlg.className = "lightbox";
  dlg.setAttribute("aria-label", "Image viewer");
  dlg.innerHTML =
    '<div class="lb-bar"><span class="lb-count" aria-live="polite"></span>' +
    '<button class="lb-btn lb-close" type="button">Close</button></div>' +
    '<div class="lb-stage"><img alt="">' +
    '<button class="lb-btn lb-prev" type="button" aria-label="Previous image">&#8592;</button>' +
    '<button class="lb-btn lb-next" type="button" aria-label="Next image">&#8594;</button></div>';
  document.body.appendChild(dlg);

  var img = dlg.querySelector("img");
  var count = dlg.querySelector(".lb-count");
  var i = 0;
  var opener = null;

  function show(n) {
    i = (n + links.length) % links.length;
    var a = links[i];
    img.src = a.getAttribute("href");
    img.alt = a.querySelector("img").alt;
    count.textContent = (i + 1) + " / " + links.length;
    // preload neighbour
    var next = new Image();
    next.src = links[(i + 1) % links.length].getAttribute("href");
  }

  links.forEach(function (a, n) {
    a.addEventListener("click", function (ev) {
      ev.preventDefault();
      opener = a;
      show(n);
      dlg.showModal();
    });
  });

  dlg.querySelector(".lb-close").addEventListener("click", function () { dlg.close(); });
  dlg.querySelector(".lb-prev").addEventListener("click", function () { show(i - 1); });
  dlg.querySelector(".lb-next").addEventListener("click", function () { show(i + 1); });
  dlg.addEventListener("close", function () { img.removeAttribute("src"); if (opener) opener.focus(); });
  dlg.addEventListener("click", function (ev) { if (ev.target === dlg || ev.target.classList.contains("lb-stage")) dlg.close(); });
  dlg.addEventListener("keydown", function (ev) {
    if (ev.key === "ArrowRight") { show(i + 1); ev.preventDefault(); }
    if (ev.key === "ArrowLeft") { show(i - 1); ev.preventDefault(); }
  });

  // Swipe on touch screens
  var x0 = null;
  dlg.addEventListener("touchstart", function (ev) { x0 = ev.touches[0].clientX; }, { passive: true });
  dlg.addEventListener("touchend", function (ev) {
    if (x0 === null) return;
    var dx = ev.changedTouches[0].clientX - x0;
    if (Math.abs(dx) > 40) show(dx < 0 ? i + 1 : i - 1);
    x0 = null;
  });
})();

// Flipbook: riffle through the thesis frames by dragging, scrolling, keys or play.
(function () {
  "use strict";
  var books = document.querySelectorAll("[data-flipbook]");
  if (!books.length) return;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  books.forEach(function (book) {
    var n = parseInt(book.getAttribute("data-frames"), 10);
    var pattern = book.getAttribute("data-src");
    var img = book.querySelector("img");
    var stage = book.querySelector(".flipbook-stage") || book;
    var range = book.querySelector(".flip-range");
    var count = book.querySelector(".flip-count");
    var play = book.querySelector(".flip-play");
    var frame = 1, timer = null, loaded = false, lastManual = 0;
    var cache = [];

    function src(i) { return pattern.replace("{n}", String(i).padStart(3, "0")); }
    function preload() {
      if (loaded) return; loaded = true;
      for (var i = 1; i <= n; i++) { var im = new Image(); im.decoding = "async"; im.src = src(i); cache[i] = im; }
    }
    function show(i) {
      i = Math.max(1, Math.min(n, Math.round(i)));
      if (i === frame) return;
      frame = i;
      img.src = src(i);
      if (range) range.value = i;
      if (count) count.textContent = i + " / " + n;
    }
    function stop() {
      clearInterval(timer); timer = null;
      if (play) { play.setAttribute("aria-pressed", "false"); play.textContent = "Flip the pages"; }
    }
    function start(loop) {
      preload();
      if (frame >= n) show(1);
      if (play) { play.setAttribute("aria-pressed", "true"); play.textContent = "Pause"; }
      var hold = 0;
      timer = setInterval(function () {
        if (frame >= n) {
          if (!loop) { stop(); return; }
          if (++hold < 14) return;
          hold = 0; frame = 0;
        }
        show(frame + 1);
      }, 70);
    }

    // Load frames when the book comes near the screen
    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) {
            preload();
            if (book.hasAttribute("data-autoplay") && !reduce && !timer) start(true);
          } else if (book.hasAttribute("data-autoplay")) { stop(); }
        });
      }, { rootMargin: "200px" });
      io.observe(book);
    } else { preload(); }

    if (play) play.addEventListener("click", function () { timer ? stop() : start(false); });
    if (range) range.addEventListener("input", function () { stop(); lastManual = Date.now(); show(+range.value); });

    // Drag: like letting pages slip from under the thumb
    if (book.querySelector(".flipbook-stage")) {
      var down = null;
      stage.addEventListener("pointerdown", function (ev) {
        stop(); preload();
        down = { x: ev.clientX, y: ev.clientY, f: frame, w: stage.clientWidth };
        stage.classList.add("is-dragging");
        stage.setPointerCapture(ev.pointerId);
      });
      stage.addEventListener("pointermove", function (ev) {
        if (!down) return;
        var d = (ev.clientX - down.x) + (ev.clientY - down.y);
        lastManual = Date.now();
        show(down.f + d / Math.max(4, down.w / 70));
      });
      ["pointerup", "pointercancel"].forEach(function (t) {
        stage.addEventListener(t, function () { down = null; stage.classList.remove("is-dragging"); });
      });
      stage.addEventListener("keydown", function (ev) {
        var k = ev.key;
        if (k === "ArrowRight" || k === "ArrowDown") { stop(); lastManual = Date.now(); show(frame + 1); ev.preventDefault(); }
        if (k === "ArrowLeft" || k === "ArrowUp") { stop(); lastManual = Date.now(); show(frame - 1); ev.preventDefault(); }
        if (k === "Home") { show(1); ev.preventDefault(); }
        if (k === "End") { show(n); ev.preventDefault(); }
      });
    }

    // Scroll: reading the introduction turns the pages
    if (book.hasAttribute("data-scroll-scrub")) {
      var grid = book.parentElement;
      var wide = window.matchMedia("(min-width: 1001px)");
      var ticking = false;
      window.addEventListener("scroll", function () {
        if (ticking || timer || !wide.matches || Date.now() - lastManual < 1500) return;
        ticking = true;
        requestAnimationFrame(function () {
          ticking = false;
          var r = grid.getBoundingClientRect();
          var span = r.height - window.innerHeight * 0.6;
          var p = span > 0 ? (-r.top + 40) / span : 0;
          show(1 + Math.max(0, Math.min(1, p)) * (n - 1));
        });
      }, { passive: true });
    }
  });
})();

// Muted looping clips: play when visible, unless the visitor prefers reduced motion
(function () {
  var clips = document.querySelectorAll("video[data-autoplay-clip]");
  if (!clips.length || window.matchMedia("(prefers-reduced-motion: reduce)").matches || !("IntersectionObserver" in window)) return;
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) { var v = en.target; if (en.isIntersecting) { var p = v.play(); if (p && p.catch) p.catch(function () {}); } else v.pause(); });
  }, { threshold: 0.3 });
  clips.forEach(function (v) { io.observe(v); });
})();
