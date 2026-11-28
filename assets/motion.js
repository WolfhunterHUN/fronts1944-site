/* FRONTS 1944: live pictures on the landing page.
   Every <video data-src> is a silent loop laid over a still picture. A loop is fetched the first time it comes on
   screen, plays while at least a quarter of it is visible, pauses when it leaves, and fades in only once it actually
   plays, so the still stays up while it loads, if autoplay is refused, or if anything fails.
   Nothing moves for visitors who ask for reduced motion or for less data. */
(function () {
  "use strict";
  var vids = document.querySelectorAll("video[data-src]");
  if (!vids.length || !("IntersectionObserver" in window)) return;
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var saveData = navigator.connection && navigator.connection.saveData;
  if (reduce || saveData) return;

  var small = window.matchMedia("(max-width: 720px)").matches;

  function load(v) {
    if (v.getAttribute("src")) return;
    v.src = (small && v.dataset.srcSm) || v.dataset.src;
    v.preload = "auto";
    v.addEventListener("playing", function () { v.classList.add("is-playing"); });
  }

  function play(v) {
    var p = v.play();
    if (p && p.catch) p.catch(function () { /* autoplay refused (e.g. power saving): the still stays */ });
  }

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      var v = e.target;      if (e.isIntersecting) load(v);
      if (e.intersectionRatio >= 0.25) play(v);
      else if (!v.paused) v.pause();
    });
  }, { threshold: [0, 0.25] });

  vids.forEach(function (v) { v.muted = true; io.observe(v); });

  document.addEventListener("visibilitychange", function () {
    if (document.hidden) vids.forEach(function (v) { if (!v.paused) v.pause(); });
    else vids.forEach(function (v) { io.unobserve(v); io.observe(v); });
  });
})();
