// app/static/js/ui/sticky_aside.js
// Make an aside fixed after scroll past a reference card, preserving layout.
(function(){
  window.UI = window.UI || {};
  var SA = {};

  SA.bind = function(opts){
    try {
      var split = document.querySelector(opts.split || '.bo-split-pane');
      var aside = document.querySelector(opts.aside || '.bo-pane-right');
      var left  = document.querySelector(opts.left || '.bo-pane-left');
      var leftCard = document.querySelector(opts.leftCard || '.bo-pane-left .card');
      if(!split || !aside || !left || !leftCard) return;

      var headerH = 56;
      try {
        var cssH = getComputedStyle(document.documentElement).getPropertyValue('--header-height');
        if(cssH) { var n = parseInt(cssH, 10); if(!isNaN(n)) headerH = n; }
      } catch(e){}
      var topOffset = headerH + (opts.gapTop || 16);

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
          left.style.paddingRight = (w + (opts.gapRight || 24)) + 'px';
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
    } catch(e) { /* no-op */ }
  };

  window.UI.stickyAside = SA;
})();
