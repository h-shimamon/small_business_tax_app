// app/static/js/ui/totalizer.js
// Sum numeric inputs inside a container and write to a target element/input.
(function(){
  window.UI = window.UI || {};
  var TZ = {};

  // opts: { container, source, target }
  TZ.bind = function(opts){
    try {
      var box = (typeof opts.container === 'string') ? document.querySelector(opts.container) : opts.container;
      if(!box) return;
      var srcSel = opts.source || 'input.form-control[type="number"]';
      var tgtSel = opts.target || '.js-total';
      var nums = Array.prototype.slice.call(box.querySelectorAll(srcSel));
      if(nums.length < 1) return;
      var total = box.querySelector(tgtSel);
      if(!total){
        var totalInput = box.querySelector('input.js-total');
        var totalDisplay = box.querySelector('.js-total');
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
    } catch(e) { /* no-op */ }
  };

  window.UI.totalizer = TZ;
})();
