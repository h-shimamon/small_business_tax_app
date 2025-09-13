"use strict";
// app/static/js/bo_preview_overlay.js
// 前面オーバーレイ(SVG)にテキストを描画・更新する最小ユーティリティ。
// 依存: なし（グローバルに window.BOPreviewOverlay を公開）
// 想定SVG: <svg class="bo-overlay-svg" viewBox="0 0 1000 1414">
(function(){
  var SVG_NS = "http://www.w3.org/2000/svg";
  var overlay = null;

  function getSvg(){
    if (!overlay) {
      overlay = document.querySelector('.bo-preview-overlay .bo-overlay-svg');
    }
    return overlay || null;
  }

  function ensureTextEl(id){
    var svg = getSvg();
    if (!svg) return null;
    var el = svg.querySelector('text[data-overlay-id="'+id+'"]');
    if (!el) {
      el = document.createElementNS(SVG_NS, 'text');
      el.setAttribute('data-overlay-id', id);
      el.setAttribute('font-size', '12');
      el.setAttribute('fill', '#111');
      el.setAttribute('dominant-baseline', 'hanging');
      el.setAttribute('font-family', 'NotoSansJP');
      svg.appendChild(el);
    }
    return el;
  }

  // xPct, yPct は 0..100 を想定（%）。内部座標 1000x1414 に変換。
  function setTextPct(id, text, xPct, yPct, opts){
    var svg = getSvg();
    if (!svg) return;
    var el = ensureTextEl(id);
    if (!el) return;
    var x = Math.max(0, Math.min(100, Number(xPct)));
    var y = Math.max(0, Math.min(100, Number(yPct)));
    // 100% -> 1000 / 1414 にスケール
    el.setAttribute('x', String(x * 10));           // 0..1000
    el.setAttribute('y', String(y * 14.14));        // 0..1414（A4縦比率）

    var fsz = (opts && typeof opts.fontSize === 'number') ? opts.fontSize : null;
    var funit = opts && opts.fontUnit ? String(opts.fontUnit).toLowerCase() : 'px';
    if (fsz != null) {
      if (funit === 'pt') { fsz = fsz * (96/72); } // pt -> px
      el.setAttribute('font-size', String(fsz));
      try { el.style.fontSize = String(fsz) + 'px'; } catch(e){}
      try { el.style.fontFamily = (opts && opts.fontFamily) ? String(opts.fontFamily) : 'NotoSansJP'; } catch(e){}
    }
    if (opts && opts.fill)     el.setAttribute('fill', String(opts.fill));
    if (opts && opts.anchor)   el.setAttribute('text-anchor', String(opts.anchor));

    el.textContent = (text == null ? '' : String(text));
  }

  function clear(id){
    var svg = getSvg();
    if (!svg) return;
    if (id) {
      var el = svg.querySelector('text[data-overlay-id="'+id+'"]');
      if (el) el.remove();
    } else {
      while (svg.lastChild) svg.removeChild(svg.lastChild);
    }
  }

  function debounce(fn, wait){
    var timer = null;
    var delay = (typeof wait === 'number' ? wait : 400);
    function wrapped(){
      var ctx = this, args = arguments;
      if (timer) clearTimeout(timer);
      timer = setTimeout(function(){
        timer = null;
        fn.apply(ctx, args);
      }, delay);
    }
    wrapped.cancel = function(){
      if (timer) { clearTimeout(timer); timer = null; }
    };
    return wrapped;
  }

  function flash(){
    try {
      var card = document.querySelector('.bo-preview-card');
      if (!card) return;
      card.classList.add('highlight');
      setTimeout(function(){ card.classList.remove('highlight'); }, 250);
    } catch(e){}
  }

  window.BOPreviewOverlay = {
    setTextPct: setTextPct,
    clear: clear,
    debounce: debounce,
    flash: flash
  };
})();
