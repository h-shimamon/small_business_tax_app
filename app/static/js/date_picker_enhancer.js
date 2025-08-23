window.DatePickerEnhancer = (function() {
  function applyYearFirstHeader(instance) {
    try {
      var cal = instance && instance.calendarContainer;
      if (!cal) return;
      var header = cal.querySelector('.flatpickr-current-month');
      if (!header) return;
      if (header.querySelector('.dp-year-select')) return; // already applied

      var yearWrap = header.querySelector('.numInputWrapper');
      var yearInput = header.querySelector('input.cur-year');
      if (!yearWrap || !yearInput) return;

      // Build year select (±10 around current year)
      var curY = instance.currentYear || new Date().getFullYear();
      var baseMin = curY - 10;
      var baseMax = curY + 10;
      var cfgMin = instance.config.minDate ? instance.config.minDate.getFullYear() : null;
      var cfgMax = instance.config.maxDate ? instance.config.maxDate.getFullYear() : null;
      var minY = (cfgMin !== null) ? Math.max(baseMin, cfgMin) : baseMin;
      var maxY = (cfgMax !== null) ? Math.min(baseMax, cfgMax) : baseMax;

      var sel = document.createElement('select');
      sel.className = 'dp-year-select';
      for (var y = maxY; y >= minY; y--) {
        var opt = document.createElement('option');
        opt.value = String(y);
        opt.textContent = y + '年';
        if (y === curY) opt.selected = true;
        sel.appendChild(opt);
      }
      sel.addEventListener('change', function() {
        var y = parseInt(this.value, 10);
        if (typeof instance.jumpToDate === 'function') {
          instance.jumpToDate(new Date(y, instance.currentMonth, 1));
        } else if (typeof instance.changeYear === 'function') {
          instance.changeYear(y);
          if (typeof instance.redraw === 'function') instance.redraw();
        }
      });

      // Hide native year field and insert our select before month dropdown (year first)
      yearWrap.style.display = 'none';
      var monthDropdown = header.querySelector('.flatpickr-monthDropdown-months');
      var insertBeforeNode = monthDropdown || yearWrap;
      header.insertBefore(sel, insertBeforeNode);
    } catch (e) {
      // no-op on failure
    }
  }

  return { applyYearFirstHeader };
})();

