// app/static/js/date_picker_init.js
// Initialize flatpickr with Japanese locale and enhancer hooks.
// Behavior matches the previous inline script in base.html.

document.addEventListener('DOMContentLoaded', function() {
  if (!window.flatpickr) return;
  var opts = {
    dateFormat: 'Y-m-d',
    altInput: true,
    altFormat: 'Y年m月d日',
    locale: flatpickr.l10ns.ja,
    allowInput: true,
    onReady: function(selectedDates, dateStr, instance) {
      if (window.DatePickerEnhancer) {
        window.DatePickerEnhancer.applyYearFirstHeader(instance);
      }
      try {
        if (instance && instance.altInput) {
          instance.altInput.placeholder = '例：2025年04月01日';
        }
      } catch (e) { /* no-op */ }
    },
    onOpen: function(selectedDates, dateStr, instance) {
      if (window.DatePickerEnhancer) {
        window.DatePickerEnhancer.applyYearFirstHeader(instance);
      }
    }
  };
  document.querySelectorAll('.nr-date-picker').forEach(function(el){
    flatpickr(el, Object.assign({ wrap: true }, opts));
  });
  document.querySelectorAll('.js-date').forEach(function(input){
    if (input.closest('.nr-date-picker')) return;
    flatpickr(input, opts);
  });
});
