/* IF Hub — the one text search.
   Used by the source pane (app.js) and the walkthrough viewer (walkthrough.html).

   These two had the same search implemented twice. The copies drifted: app.js marked
   only the first match in each text node while walkthrough.html marked them all (#112),
   and the highlight colours diverged. One implementation, parameterised by the three
   things that genuinely differ between the pages — where to look, what to look in, and
   how short a query is allowed (#114).

   createSearch({ input, container, selector, minLength, debounceMs }) -> controller

     input      the <input> to bind. Listeners are bound once, here.
     container  element, or a function returning one. Resolved per search, so a pane
                that re-renders is always searched as it is now.
     selector   which descendants of the container to search within.
     minLength  shortest query that searches at all. Default 2.
     debounceMs typing settle time. Default 200.

   The controller exposes clear(), search(q), next(), prev() and refresh(). refresh()
   re-runs the current query against freshly rendered content — what a pane wants after
   swapping its own contents. */

function createSearch(opts) {
  var input = opts.input;
  var selector = opts.selector;
  var minLength = opts.minLength || 2;
  var debounceMs = opts.debounceMs || 200;
  var hits = [];
  var cur = -1;
  var debounceTimer;

  function container() {
    return typeof opts.container === 'function' ? opts.container() : opts.container;
  }

  function clear() {
    var el = container();
    if (!el) return;
    el.querySelectorAll('.search-hit').forEach(function(hit) {
      hit.outerHTML = hit.textContent;
    });
    hits = [];
    cur = -1;
  }

  /* Mark every occurrence in each text node, not just the first. Walk forward through
     one node and replace it once: splitting at the first match and re-inserting the
     remainder left that remainder unscanned, because the TreeWalker had already
     collected its node list (#112). */
  function markMatches(el, q) {
    if (!q) return;
    var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    var nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    var lower = q.toLowerCase();
    nodes.forEach(function(node) {
      var text = node.textContent;
      if (text.toLowerCase().indexOf(lower) === -1) return;
      var frag = document.createDocumentFragment();
      var pos = 0;
      for (;;) {
        var idx = text.toLowerCase().indexOf(lower, pos);
        if (idx === -1) break;
        if (idx > pos) frag.appendChild(document.createTextNode(text.slice(pos, idx)));
        var span = document.createElement('span');
        span.className = 'search-hit';
        // slice from text, not q, so the hit keeps the source's own casing
        span.textContent = text.slice(idx, idx + q.length);
        frag.appendChild(span);
        pos = idx + q.length;
      }
      if (pos < text.length) frag.appendChild(document.createTextNode(text.slice(pos)));
      node.parentNode.replaceChild(frag, node);
    });
  }

  function select(i) {
    if (!hits.length) return;
    if (cur >= 0 && hits[cur]) hits[cur].classList.remove('search-current');
    cur = (i + hits.length) % hits.length;
    hits[cur].classList.add('search-current');
    hits[cur].scrollIntoView({ block: 'center' });
  }

  function search(q) {
    clear();
    var el = container();
    if (!el || !q || q.length < minLength) return;
    var lower = q.toLowerCase();
    el.querySelectorAll(selector).forEach(function(target) {
      if (target.textContent.toLowerCase().indexOf(lower) !== -1) markMatches(target, q);
    });
    hits = Array.prototype.slice.call(el.querySelectorAll('.search-hit'));
    select(0);
  }

  input.addEventListener('input', function() {
    clearTimeout(debounceTimer);
    var self = this;
    debounceTimer = setTimeout(function() { search(self.value); }, debounceMs);
  });

  input.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      select(cur + (e.shiftKey ? -1 : 1));
    }
    if (e.key === 'Escape') {
      clear();
      this.value = '';
      this.blur();
    }
  });

  return {
    clear: clear,
    search: search,
    next: function() { select(cur + 1); },
    prev: function() { select(cur - 1); },
    /* Re-run whatever is in the box against content that has just been re-rendered. */
    refresh: function() { search(input.value); }
  };
}
