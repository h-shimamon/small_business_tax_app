// app/static/js/ui/radios_toggle.js
// Allow radio groups to toggle off when re-clicking the checked option.
(function(){
  window.UI = window.UI || {};
  var RT = {};

  RT.enableUncheckOnReclickByName = function(name){
    try {
      var radios = document.querySelectorAll('input[type="radio"][name="'+name+'"]');
      radios.forEach(function(el){
        el.addEventListener('mousedown', function(){ this._wasChecked = this.checked; });
        el.addEventListener('click', function(){ if (this._wasChecked) { this.checked = false; } });
      });
    } catch(e) { /* no-op */ }
  };

  window.UI.radiosToggle = RT;
})();
