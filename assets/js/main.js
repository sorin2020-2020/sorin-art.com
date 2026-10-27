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
