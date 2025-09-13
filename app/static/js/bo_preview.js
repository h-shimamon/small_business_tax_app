(function(){
  const g = (typeof window !== 'undefined') ? window : this;

  function createStore(){
    const st = {
      overlay: null,
      mapping: {},
      values: {},
      nodes: new Map(),
      paused: false,
      debounceMs: 400,
      _debounceId: null,
    };

    function setOverlay(el){ st.overlay = el || null; if(st.overlay){ st.overlay.classList.add('is-on'); } }
    function setMapping(mp){ st.mapping = mp || {}; }
    function setPaused(v){ st.paused = !!v; }
    function setDebounce(ms){ const n = Number(ms); if(!Number.isNaN(n) && n >= 0) st.debounceMs = n; }

    function _textForInput(el){
      if(!el) return '';
      const t = (el.getAttribute('data-text') || '').trim();
      if(t) return t;
      if(el.type === 'checkbox' || el.type === 'radio'){
        const id = el.id;
        if(id){ const lab = document.querySelector('label[for="'+id+'"]'); if(lab) return (lab.textContent||'').trim(); }
        return (el.value || '').trim();
      }
      return (el.value || '').trim();
    }

    function _collectFromInputs(root){
      const scope = root || document;
      const els = scope.querySelectorAll('[data-key]');
      const bag = {};
      els.forEach(function(el){
        const key = el.getAttribute('data-key');
        if(!key) return;
        if(el.type === 'checkbox'){
          if(!bag[key]) bag[key] = [];
          if(el.checked) bag[key].push(_textForInput(el));
        } else if(el.type === 'radio'){
          if(el.checked) bag[key] = _textForInput(el);
          else if(!bag[key]) bag[key] = '';
        } else {
          bag[key] = _textForInput(el);
        }
      });
      st.values = bag;
    }

    function _ensureNode(key){
      if(!st.overlay) return null;
      let node = st.nodes.get(key);
      if(!node){
        node = document.createElement('div');
        node.className = 'bo-mark';
        node.setAttribute('data-mark', key);
        st.overlay.appendChild(node);
        st.nodes.set(key, node);
      }
      return node;
    }

    function _applyStyle(node, conf){
      if(!node || !conf) return;
      const x = Number(conf.x)||0, y = Number(conf.y)||0;
      node.style.left = x + '%';
      node.style.top = y + '%';
      const align = String(conf.align||'left');
      if(align === 'center'){ node.style.transform = 'translate(-50%, -50%)'; node.style.textAlign = 'center'; }
      else if(align === 'right'){ node.style.transform = 'translate(-100%, -50%)'; node.style.textAlign = 'right'; }
      else { node.style.transform = 'translate(0, -50%)'; node.style.textAlign = 'left'; }
      if(conf.fontSize) node.style.fontSize = String(conf.fontSize);
      if(conf.weight) node.style.fontWeight = String(conf.weight);
      if(conf.color) node.style.color = String(conf.color);
      if(conf.letterSpacing) node.style.letterSpacing = String(conf.letterSpacing);
    }

    function _formatValue(val, conf){
      if(val == null) return '';
      if(Array.isArray(val)){
        const sep = (conf && conf.joinWith) ? String(conf.joinWith) : '、';
        return val.join(sep);
      }
      return String(val);
    }

    function render(){
      if(st.paused || !st.overlay) return;
      Object.keys(st.mapping).forEach(function(key){
        const conf = st.mapping[key];
        const raw = st.values[key];
        const text = _formatValue(raw, conf);
        const node = _ensureNode(key);
        if(!node) return;
        node.textContent = text;
        _applyStyle(node, conf);
        node.style.display = text ? 'block' : 'none';
      });
    }

    function _scheduleRender(){
      if(st.paused) return;
      if(st._debounceId) cancelAnimationFrame(st._debounceId);
      const wait = Math.max(0, st.debounceMs);
      if(wait === 0){ render(); return; }
      const t0 = performance.now();
      st._debounceId = requestAnimationFrame(function step(){
        if(performance.now() - t0 >= wait){ render(); }
        else { st._debounceId = requestAnimationFrame(step); }
      });
    }

    function bind(root){
      const scope = root || document;
      const onChangeImmediate = function(){ _collectFromInputs(scope); render(); };
      const onChangeDebounced = function(){ _collectFromInputs(scope); _scheduleRender(); };

      scope.addEventListener('change', function(e){
        const el = e.target;
        if(!(el instanceof HTMLElement)) return;
        if(!el.hasAttribute('data-key')) return;
        if(el.getAttribute('data-commit') === 'blur') return;
        if(el instanceof HTMLInputElement && (el.type === 'radio' || el.type === 'checkbox')){ onChangeImmediate(); }
        else { onChangeDebounced(); }
      }, true);

      scope.addEventListener('input', function(e){
        const el = e.target;
        if(!(el instanceof HTMLElement)) return;
        if(!el.hasAttribute('data-key')) return;
        if(el instanceof HTMLInputElement && (el.type === 'text' || el.type === 'number' || el.type === 'search')){
          if(el.getAttribute('data-commit') === 'blur') return;
          onChangeDebounced();
        }
      }, true);

      scope.addEventListener('blur', function(e){
        const el = e.target;
        if(!(el instanceof HTMLElement)) return;
        if(!el.hasAttribute('data-key')) return;
        if(el.getAttribute('data-commit') === 'blur'){ onChangeImmediate(); }
      }, true);

      _collectFromInputs(scope);
      render();
    }

    return { setOverlay, setMapping, setPaused, setDebounce: setDebounce, bind, render };
  }

  const api = createStore();
  g.boPreview = api;
})();
