"use strict";
// app/static/js/bo_preview_overlay_bindings.js (robust)
// 入力要素の data-overlay-id と API (/company/filings/overlay) を使って
// 前面SVGにテキストを描画。pt指定補正やローカル微調整、フェイルセーフ内蔵。
(function(){
  var mod = window.BOPreviewOverlay;
  if(!mod) return;

  var PT2PX = 96/72;

  function toNumber(v, d){ var n = Number(v); return (typeof n === 'number' && isFinite(n)) ? n : d; }
  function clamp01p(v){ return Math.max(0, Math.min(100, v)); }

  function getSvg(){ return document.querySelector('.bo-preview-overlay .bo-overlay-svg'); }
  function getHost(){ return document.querySelector('.bo-preview-overlay'); }
  function getBox(){ return document.querySelector('.bo-preview-box'); }

  function pxXtoPct(px){
    var svg = getSvg();
    var w = svg && svg.clientWidth ? svg.clientWidth : 0;
    var n = Number(px);
    if (w > 0 && isFinite(n)) return (n / w) * 100; // CSS px -> % of width
    return n / 10; // fallback for 1000 width viewBox
  }
  function pxYtoPct(px){
    var svg = getSvg();
    var h = svg && svg.clientHeight ? svg.clientHeight : 0;
    var n = Number(px);
    if (h > 0 && isFinite(n)) return (n / h) * 100; // CSS px -> % of height
    return n / 14.14; // fallback for 1414 height viewBox
  }

  function cacheKeyFor(page, idx){ return 'bo_overlay_cfg_' + page + '_' + idx; }
  function saveCfgCache(page, idx, obj){
    try { localStorage.setItem(cacheKeyFor(page, idx), JSON.stringify(obj||{})); } catch(e){}
  }
  function loadCfgCache(page, idx){
    try {
      var s = localStorage.getItem(cacheKeyFor(page, idx));
      return s ? (JSON.parse(s)||{}) : {};
    } catch(e){ return {}; }
  }

  function fetchOverlayConfig(){
    try {
      var overlayHost = getHost();
      if(!overlayHost) return Promise.resolve({});
      var page = overlayHost.getAttribute('data-overlay-page') || '';
      var year = overlayHost.getAttribute('data-overlay-year') || '2025';
      var idx  = overlayHost.getAttribute('data-overlay-idx') || '1';
      if(!page) return Promise.resolve({});
      var url = (overlayHost.getAttribute('data-overlay-url') || '/company/filings/overlay') +
        '?page=' + encodeURIComponent(page) +
        '&year=' + encodeURIComponent(year) +
        '&idx=' + encodeURIComponent(idx) +
        '&_ts=' + Date.now();
      return fetch(url, { credentials: 'same-origin' })
        .then(function(r){ return (r && r.ok) ? r.json() : null; })
        .then(function(j){
          if (j && j.items && Array.isArray(j.items)) {
            saveCfgCache(page, idx, j);
            return j;
          }
          // fallback to cache
          var c = loadCfgCache(page, idx);
          return c && c.items ? c : {};
        })
        .catch(function(){
          var c = loadCfgCache(page, idx);
          return c && c.items ? c : {};
        });
    } catch(e){ return Promise.resolve({}); }
  }

  function whenReadyToDraw(cb){
    var box = getBox();
    var svg = getSvg();
    var tries = 30;
    function ok(){ return (svg && svg.clientWidth > 0 && svg.clientHeight > 0) || (box && box.classList.contains('is-img-ready')); }
    (function wait(){
      if (ok()) { try { cb(); } catch(_){} return; }
      if (tries-- <= 0) { try { cb(); } catch(_){} return; }
      setTimeout(wait, 50);
    })();
  }

  function bindAll(apiMap){
    var nodes = document.querySelectorAll('[data-overlay-id]');
    nodes.forEach(function(el){ bindOne(el, apiMap); });
  }

  function bindOne(el, apiMap){
    var id = el.getAttribute('data-overlay-id');
    if(!id) return;

    var apiItem = (apiMap && apiMap[id]) || null;
    var x = (apiItem && typeof apiItem.x_pct === 'number') ? apiItem.x_pct : toNumber(el.getAttribute('data-x'), 0);
    var y = (apiItem && typeof apiItem.y_pct === 'number') ? apiItem.y_pct : toNumber(el.getAttribute('data-y'), 0);
    var font = (apiItem && typeof apiItem.font_size === 'number') ? apiItem.font_size : toNumber(el.getAttribute('data-font'), 12);
    var fontUnit = (apiItem && apiItem.font_unit) ? String(apiItem.font_unit) : (el.getAttribute('data-font-unit') || 'px');

    var dx_pt = toNumber(apiItem && apiItem.dx_pt, 0);
    var dy_pt = toNumber(apiItem && apiItem.dy_pt, 0);
    var dx_px = toNumber(el.getAttribute('data-dx'), 0) + toNumber(apiItem && apiItem.dx_px, 0) + dx_pt * PT2PX;
    var dy_px = toNumber(el.getAttribute('data-dy'), 0) + toNumber(apiItem && apiItem.dy_px, 0) + dy_pt * PT2PX;

    function applyCore(){
      var xEff = clamp01p(x + pxXtoPct(dx_px));
      var yEff = clamp01p(y + pxYtoPct(dy_px));
      mod.setTextPct(id, el && typeof el.value !== 'undefined' ? el.value : '', xEff, yEff, {fontSize: font, fontUnit: fontUnit, fontFamily: 'NotoSansJP'});
    }
    function apply(){ whenReadyToDraw(applyCore); }

    function getStoreKey(){
      var host = getHost();
      var page = host && host.getAttribute('data-overlay-page') || '';
      var idx  = host && host.getAttribute('data-overlay-idx') || '1';
      return 'bo_adj_' + page + '_' + idx + '_' + id;
    }
    function loadAdj(){
      try {
        var s = localStorage.getItem(getStoreKey());
        if(!s) return {dx_pt:0, dy_pt:0};
        var o = JSON.parse(s) || {};
        return { dx_pt: toNumber(o.dx_pt, 0), dy_pt: toNumber(o.dy_pt, 0) };
      } catch(e){ return {dx_pt:0, dy_pt:0}; }
    }
    function saveAdj(a){
      try { localStorage.setItem(getStoreKey(), JSON.stringify({ dx_pt: toNumber(a.dx_pt,0), dy_pt: toNumber(a.dy_pt,0) })); } catch(e){}
    }

    var adj = loadAdj();
    dx_px += adj.dx_pt * PT2PX;
    dy_px += adj.dy_pt * PT2PX;

    if (el.getAttribute('data-overlay-bound') !== '1'){
      var tag  = (el.tagName || '').toLowerCase();
      var type = (el.getAttribute('type') || '').toLowerCase();
      if(tag === 'input' && (type === 'radio' || type === 'checkbox')){
        el.addEventListener('change', apply, {passive:true});
      } else {
        var deb = mod.debounce(apply, 400);
        el.addEventListener('input', deb);
        el.addEventListener('blur', function(){ deb.cancel(); apply(); });
        el.addEventListener('change', function(){ deb.cancel(); apply(); });
        el.addEventListener('compositionend', function(){ deb.cancel(); apply(); });
      }

      // Mac friendly nudge: Option(+Ctrl)+Arrows, Shift=5pt. Reset: Option+R or Escape.
      function handleNudge(e){
        var isTarget = (document.activeElement === el) || (e.target === el);
        if (!isTarget) return;
        var alt = !!e.altKey; var ctrlAlt = alt && !!e.ctrlKey;
        if (!(alt || ctrlAlt)) return;
        var step = e.shiftKey ? 5 : 0.5; // pt
        var used = false;
        if (e.key === 'ArrowLeft') { adj.dx_pt -= step; dx_px -= step * PT2PX; used = true; }
        else if (e.key === 'ArrowRight') { adj.dx_pt += step; dx_px += step * PT2PX; used = true; }
        else if (e.key === 'ArrowUp') { adj.dy_pt -= step; dy_px -= step * PT2PX; used = true; }
        else if (e.key === 'ArrowDown') { adj.dy_pt += step; dy_px += step * PT2PX; used = true; }
        else if (e.key === 'r' || e.key === 'R' || e.key === 'Escape') {
          // reset to API/base values
          adj.dx_pt = 0; adj.dy_pt = 0;
          dx_px = toNumber(el.getAttribute('data-dx'), 0) + toNumber(apiItem && apiItem.dx_px, 0) + dx_pt * PT2PX;
          dy_px = toNumber(el.getAttribute('data-dy'), 0) + toNumber(apiItem && apiItem.dy_px, 0) + dy_pt * PT2PX;
          used = true;
        }
        if (used) {
          e.preventDefault();
          e.stopPropagation();
          saveAdj(adj);
          apply();
          try { if (mod && mod.flash) mod.flash(); } catch(_){}
        }
      }
      el.addEventListener('keydown', handleNudge, {passive:false, capture:true});
      document.addEventListener('keydown', handleNudge, {passive:false, capture:true});

      el.setAttribute('data-overlay-bound', '1');
    }

    apply();
  }

  function reload(){
    return fetchOverlayConfig().then(function(cfg){
      var map = {};
      try { (cfg.items || []).forEach(function(it){ if(it && it.id) map[it.id] = it; }); } catch(e){}
      bindAll(map);
      return map;
    });
  }

  // expose
  window.BOPreviewOverlayBindings = {
    reload: reload,
    dumpAdjustments: function(){
      try {
        var host = getHost();
        var page = host && host.getAttribute('data-overlay-page') || '';
        var idx  = host && host.getAttribute('data-overlay-idx') || '1';
        var nodes = document.querySelectorAll('[data-overlay-id]');
        var out = {};
        nodes.forEach(function(el){
          var id = el.getAttribute('data-overlay-id');
          if(!id) return;
          var key = 'bo_adj_' + page + '_' + idx + '_' + id;
          try {
            var s = localStorage.getItem(key);
            if(!s) return;
            var o = JSON.parse(s)||{};
            var dx = Number(o.dx_pt)||0;
            var dy = Number(o.dy_pt)||0;
            if (dx || dy) out[id] = { dx_pt: dx, dy_pt: dy };
          } catch(e){}
        });
        return { page: page, idx: String(idx), items: out };
      } catch(e){ return { page:'', idx:'', items:{} }; }
    }
  };
})();