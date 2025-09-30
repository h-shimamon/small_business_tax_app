(function(){
  'use strict';
  function setExpanded(headerTr, expanded){
    if(!headerTr) return;
    var id = headerTr.getAttribute('data-sec') || '';
    var btn = headerTr.querySelector('.pl-toggle');
    if(btn){
      btn.setAttribute('aria-expanded', expanded ? 'true' : 'false');
      btn.textContent = expanded ? '▼' : '▶';
    }
    // toggle rows until the section total row (class contains both total-row and middle-total)
    var row = headerTr.nextElementSibling;
    while(row){
      if(row.classList && row.classList.contains('middle-header')) break; // next section
      var isSectionTotal = row.classList && row.classList.contains('total-row') && row.classList.contains('middle-total');
      if(isSectionTotal) break;
      if(row.tagName === 'TR'){
        row.style.display = expanded ? 'table-row' : 'none';
      }
      row = row.nextElementSibling;
    }
  }
  function init(){
    // collapse all on load
    var headers = document.querySelectorAll('tr.middle-header[data-sec]');
    headers.forEach(function(tr){ setExpanded(tr, false); });
    document.addEventListener('click', function(e){
      var t = e.target;
      if(t && t.classList && t.classList.contains('pl-toggle')){
        e.preventDefault();
        var tr = t.closest('tr.middle-header');
        var isOpen = t.getAttribute('aria-expanded') === 'true';
        setExpanded(tr, !isOpen);
      }
    });
  }
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();