// app/static/js/pages/filings_business_overview.js
// Externalized scripts for business_overview_1 page.
// Behavior is unchanged from inline versions.

(function(){
  // Allow radio to toggle off by clicking selected option again
  var radios = document.querySelectorAll('input[type="radio"][name="trade_type"]');
  radios.forEach(function(el){
    el.addEventListener('mousedown', function(){ this._wasChecked = this.checked; });
    el.addEventListener('click', function(){ if (this._wasChecked) { this.checked = false; } });
  });
})();

(function(){
  // Sync segmented checkbox labels with checked state and enable label toggling
  var checks = document.querySelectorAll('input[type="checkbox"][name="trade_type_other"]');
  function syncOne(el){
    var lab = document.querySelector('label[for="'+el.id+'"]');
    if(lab){ lab.classList.toggle('is-checked', el.checked); }
  }
  checks.forEach(function(el){
    el.addEventListener('change', function(){ syncOne(el); });
    syncOne(el);
  });
  var labels = document.querySelectorAll('label[for^="trade_other_"]');
  labels.forEach(function(lab){
    lab.addEventListener('click', function(e){
      e.preventDefault();
      var id = this.getAttribute('for');
      var el = document.getElementById(id);
      if(!el) return;
      el.checked = !el.checked;
      el.dispatchEvent(new Event('change', {bubbles:true}));
    });
  });
})();

(function(){
  // Sticky aside behavior for the preview pane
  var split = document.querySelector('.bo-split-pane');
  var aside = document.querySelector('.bo-pane-right');
  var left  = document.querySelector('.bo-pane-left');
  var leftCard = document.querySelector('.bo-pane-left .card');
  if(!split || !aside || !left || !leftCard) return;

  var headerH = 56;
  try {
    var cssH = getComputedStyle(document.documentElement).getPropertyValue('--header-height');
    if(cssH) { var n = parseInt(cssH, 10); if(!isNaN(n)) headerH = n; }
  } catch(e){}
  var topOffset = headerH + 16;

  var gutterBase = null;
  var wasFixed = false;

  function computeGutter(splitRect, asideRect){
    return Math.round((splitRect.left + splitRect.width) - (asideRect.left + asideRect.width));
  }
  function computeLeftForFixed(splitRect, asideWidth){
    var pageX = window.pageXOffset || document.documentElement.scrollLeft || 0;
    var gutter = (gutterBase == null ? 0 : gutterBase);
    return Math.round(splitRect.left + pageX + split.clientWidth - asideWidth - gutter);
  }

  function tick(){
    var splitRect = split.getBoundingClientRect();
    var asideRect = aside.getBoundingClientRect();
    var w = asideRect.width;
    var start = leftCard.getBoundingClientRect().top + window.pageYOffset;
    var sc = window.pageYOffset + topOffset;

    if(!wasFixed){
      gutterBase = computeGutter(splitRect, asideRect);
    }
    if(sc >= start){
      aside.style.position = 'fixed';
      aside.style.top = topOffset + 'px';
      aside.style.width = w + 'px';
      aside.style.left = computeLeftForFixed(splitRect, w) + 'px';
      left.style.paddingRight = (w + 24) + 'px';
      wasFixed = true;
    } else {
      aside.style.position = '';
      aside.style.top = '';
      aside.style.left = '';
      aside.style.width = '';
      left.style.paddingRight = '';
      wasFixed = false;
    }
  }
  window.addEventListener('scroll', tick, {passive:true});
  window.addEventListener('resize', function(){
    var was = wasFixed;
    aside.style.position = '';
    aside.style.left = '';
    wasFixed = false;
    tick();
    if(was){ tick(); }
  });
  tick();
})();

(function(){
  // Auto-sum worker counts into total cell
  var container = document.querySelector('.js-workers-count');
  if(!container) return;
  var srcSel = container.getAttribute('data-total-source') || 'input.form-control[type="number"]';
  var tgtSel = container.getAttribute('data-total-target') || '.js-total';
  var nums = Array.prototype.slice.call(container.querySelectorAll(srcSel));
  if(nums.length < 1) return;
  var total = container.querySelector(tgtSel);
  if(!total){
    var totalInput = container.querySelector('input.js-total');
    var totalDisplay = container.querySelector('.js-total');
    total = totalInput || totalDisplay || nums[nums.length - 1];
  }
  if(!total) return;
  if(total.tagName === 'INPUT'){
    total.readOnly = true;
    total.setAttribute('aria-readonly', 'true');
  }
  function toNumber(el){
    var v = (el.value || '').replace(/,/g,'').trim();
    if(v === '') return 0;
    var n = Number(v);
    return isFinite(n) ? n : 0;
  }
  function recalc(){
    var sum = 0;
    for(var i=0;i<nums.length;i++){
      var el = nums[i];
      if(el === total) continue;
      sum += toNumber(el);
    }
    var s = String(sum);
    if(total.tagName === 'INPUT'){
      if(s !== total.value){ total.value = s; }
    } else {
      if(s !== total.textContent){ total.textContent = s; }
    }
  }
  nums.forEach(function(el){ if(el !== total){ el.addEventListener('input', recalc); }});
  recalc();
})();

(function(){
  // Toggle helper input for PC OS "other"
  var other = document.getElementById('pc_os_other');
  var wrap = document.querySelector('.bo-os-other-field');
  var grid = document.querySelector('.bo-os-other-grid');
  if(!other) return;
  function sync(){
    var on = !!other.checked;
    if(wrap) wrap.classList.toggle('is-visible', on);
    if(grid) grid.classList.toggle('is-on', on);
  }
  other.addEventListener('change', sync);
  sync();
})();

(function(){
  // Toggle helper input for trade "other"
  var other = document.getElementById('trade_other_other');
  var wrap = document.querySelector('.bo-trade-other-field');
  var grid = document.querySelector('.bo-trade-other-input');
  if(!other) return;
  function sync(){
    var on = !!other.checked;
    if(wrap) wrap.classList.toggle('is-visible', on);
    if(grid) grid.classList.toggle('is-on', on);
  }
  other.addEventListener('change', sync);
  sync();
})();
