// app/static/js/ui/segmented.js
// Minimal, safe helpers for segmented controls. No auto-run.
(function(){
  window.UI = window.UI || {};
  var Seg = {};

  // Add/remove 'is-checked' on labels for a checkbox group by name
  Seg.syncCheckboxLabelStateByName = function(name){
    try {
      var checks = document.querySelectorAll('input[type="checkbox"][name="'+name+'"]');
      function syncOne(el){
        var lab = document.querySelector('label[for="'+el.id+'"]');
        if(lab){ lab.classList.toggle('is-checked', el.checked); }
      }
      checks.forEach(function(el){
        el.addEventListener('change', function(){ syncOne(el); });
        syncOne(el);
      });
    } catch(e) { /* no-op */ }
  };

  // Enable clicking labels whose for="<prefix>..." to toggle the associated input
  Seg.enableLabelToggleByForPrefix = function(prefix){
    try {
      var labels = document.querySelectorAll('label[for^="'+prefix+'"]');
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
    } catch(e) { /* no-op */ }
  };

  window.UI.segmented = Seg;
})();
