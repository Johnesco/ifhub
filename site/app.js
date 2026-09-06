/* IF Hub — split-pane player. Markup lives in app.html; styles in app.css; shared helpers in
   themes.js (themes) and hub.js (data loading, collections). */

/* ==================================================================
   CONFIG
   ================================================================== */
var CONFIG = {
  MIN_PANE_WIDTH: 200,
  SEARCH_MIN_LENGTH: 2,
  SEARCH_DEBOUNCE_MS: 200,
  DEFAULT_VOLUME: 70,
  IFRAME_THEME_DELAY_MS: 500
};

/* ==================================================================
   STATE
   ================================================================== */
var games = [];       // populated from games.json
var gameMap = {};     // id → game entry
var currentGame = '';
var currentView = 'source';
var sourceCache = {};

/* ==================================================================
   INIT
   ================================================================== */
document.addEventListener('DOMContentLoaded', function() {
  loadHubData('games.json').then(function(data) {
    var allGames = data.entries;
    var hubs = data.hubs;

    // Filter the game list to the hub encoded in the current URL.
    function applyHubFilter() {
      var activeHub = resolveHub(hubs).activeHub;
      games = activeHub
        ? allGames.filter(function(g) { return matchesHub(g, activeHub); })
        : allGames.slice();
      games.sort(function(a, b) { return a.title.localeCompare(b.title); });
      gameMap = {};
      games.forEach(function(g) { gameMap[g.id] = g; });
      return activeHub;
    }

    function updateLibraryLink(activeHub) {
      document.getElementById('library-link').href =
        (activeHub && activeHub.id !== 'all') ? 'index.html?hub=' + activeHub.id : 'index.html';
    }

    var activeHub = applyHubFilter();
    buildDropdown();
    bindUI();
    initSoundControls();

    // Build hub selector dropdown
    var hubSelect = document.getElementById('hub-select');
    hubs.forEach(function(h) {
      var opt = document.createElement('option');
      opt.value = h.id;
      opt.textContent = h.title;
      hubSelect.appendChild(opt);
    });
    hubSelect.value = activeHub ? activeHub.id : 'all';

    // Collection change: re-filter the game list in place, no page reload.
    // Keep the current game loaded if it still belongs to the new collection,
    // otherwise fall back to the first game in the new collection.
    //
    // Uses replaceState (not pushState): the player iframe (Parchment) injects
    // its own session-history entries, so top-level pushState back/forward is
    // unreliable here. replaceState keeps the URL shareable without competing
    // with the iframe's history; browser Back then returns to the prior page.
    hubSelect.addEventListener('change', function() {
      var v = hubSelect.value;
      history.replaceState(null, '', 'app.html' + (v && v !== 'all' ? '?hub=' + v : ''));
      var ah = applyHubFilter();
      buildDropdown();
      updateLibraryLink(ah);
      if (gameMap[currentGame]) {
        document.getElementById('game-select').value = currentGame;
      } else if (games.length) {
        switchGame(games[0].id);
      }
    });

    updateLibraryLink(activeHub);

    buildStyleDropdown(null);

    var params = new URLSearchParams(window.location.search);
    var initGame = params.get('game') || (games.length ? games[0].id : '');
    if (!gameMap[initGame] && games.length) initGame = games[0].id;
    if (initGame) switchGame(initGame);
    var savedView = params.get('view');
    applyView(savedView || 'game');
  }).catch(function(err) {
    showLoadError(null, err);
  });
});

/* ==================================================================
   BUILD DROPDOWN FROM games.json
   ================================================================== */
function buildDropdown() {
  var sel = document.getElementById('game-select');
  sel.innerHTML = '';
  games.forEach(function(g) {
    var opt = document.createElement('option');
    opt.value = g.id;
    opt.textContent = g.title;
    sel.appendChild(opt);
  });
}

/* ==================================================================
   BIND UI (once)
   ================================================================== */
function bindUI() {
  // View toggle buttons
  document.getElementById('view-toggles').addEventListener('click', function(e) {
    var btn = e.target.closest('.view-toggle');
    if (!btn) return;
    var pane = btn.dataset.pane;
    handleToggleClick(pane);
  });

  // Ctrl+F shortcut
  document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
      if (!document.body.classList.contains('source-collapsed')) {
        e.preventDefault();
        var input = document.getElementById('search-source');
        input.focus();
        input.select();
      }
    }
  });

  // Snapshot game width so it stays fixed as window grows
  var gamePane = document.getElementById('game-pane');
  document.body.style.setProperty('--game-width', gamePane.offsetWidth + 'px');

  // Resize handle drag
  var handle = document.getElementById('resize-handle');
  handle.addEventListener('mousedown', startResize);
  handle.addEventListener('touchstart', startResize, { passive: false });

  function startResize(e) {
    e.preventDefault();
    handle.classList.add('dragging');
    document.body.classList.add('resizing');

    var onMove = function(e) {
      var x = e.touches ? e.touches[0].clientX : e.clientX;
      var w = document.body.clientWidth;
      var gameW = Math.max(CONFIG.MIN_PANE_WIDTH, Math.min(x, w - CONFIG.MIN_PANE_WIDTH));
      document.body.style.setProperty('--game-width', gameW + 'px');
    };

    var onUp = function() {
      handle.classList.remove('dragging');
      document.body.classList.remove('resizing');
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      document.removeEventListener('touchmove', onMove);
      document.removeEventListener('touchend', onUp);
    };

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
    document.addEventListener('touchmove', onMove, { passive: false });
    document.addEventListener('touchend', onUp);
  }

  // Game selector dropdown
  document.getElementById('game-select').addEventListener('change', function() {
    if (this.value !== currentGame) switchGame(this.value);
  });

  // Hamburger menu toggle
  var hamBtn = document.getElementById('hamburger-btn');
  var hamMenu = document.getElementById('hamburger-menu');
  hamBtn.addEventListener('click', function(e) {
    e.stopPropagation();
    hamMenu.classList.toggle('open');
  });
  document.addEventListener('click', function() {
    hamMenu.classList.remove('open');
  });
  hamMenu.addEventListener('click', function(e) {
    hamMenu.classList.remove('open');
  });

  // Full Page — navigate to game's own play page
  document.getElementById('btn-fullpage').addEventListener('click', function(e) {
    e.preventDefault();
    var g = gameMap[currentGame];
    if (g && g.playUrl) {
      var sel = document.getElementById('style-select');
      var themeId = (sel && sel.value !== 'overlay') ? sel.value : '';
      var url = g.playUrl;
      if (themeId && themeId !== 'classic') {
        url += (url.indexOf('?') === -1 ? '?' : '&') + 'theme=' + themeId;
      }
      window.location.href = url;
    }
  });
}

/* ==================================================================
   UTILITY
   ================================================================== */
function esc(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/* ==================================================================
   INFORM 7 SYNTAX HIGHLIGHTER
   ================================================================== */
var I7_HEADING = /^(Volume|Book|Part|Chapter|Section)\s+(.+)/;

function highlightInform(line) {
  if (I7_HEADING.test(line)) return '<span class="syn-head">' + esc(line) + '</span>';
  if (/^Table\s+/.test(line)) return '<span class="syn-tbl">' + esc(line) + '</span>';

  var out = '', state = 'normal', depth = 0, buf = '';

  function flush(cls) {
    if (!buf) return;
    if (cls) out += '<span class="' + cls + '">' + esc(buf) + '</span>';
    else out += esc(buf);
    buf = '';
  }

  for (var i = 0; i < line.length; i++) {
    var ch = line[i];
    if (state === 'normal') {
      if (ch === '"') { flush(); buf = ch; state = 'string'; }
      else if (ch === '[') { flush(); buf = ch; depth = 1; state = 'comment'; }
      else buf += ch;
    } else if (state === 'string') {
      buf += ch;
      if (ch === '[') {
        var before = buf.slice(0, -1);
        if (before) out += '<span class="syn-str">' + esc(before) + '</span>';
        buf = ch; state = 'sub'; depth = 1;
      } else if (ch === '"') { flush('syn-str'); state = 'normal'; }
    } else if (state === 'sub') {
      buf += ch;
      if (ch === '[') depth++;
      else if (ch === ']') { depth--; if (!depth) { flush('syn-sub'); state = 'string'; } }
    } else if (state === 'comment') {
      buf += ch;
      if (ch === '[') depth++;
      else if (ch === ']') { depth--; if (!depth) { flush('syn-cmt'); state = 'normal'; } }
    }
  }

  if (state === 'string') flush('syn-str');
  else if (state === 'comment') flush('syn-cmt');
  else if (state === 'sub') flush('syn-sub');
  else {
    if (buf) out += highlightI7Keywords(esc(buf));
    buf = '';
  }

  if (state === 'normal' && !out.includes('<span')) return highlightI7Keywords(esc(line));
  return out;
}

function highlightI7Keywords(html) {
  html = html.replace(/\b(Understand|understand|Instead of|Instead|instead of|instead|After|after|Before|before|Check|check|Carry out|carry out|Report|report|Every turn|every turn|When play begins|When|when|Rule|rule|This is|Definition|definition|To say|To decide|To |say |now |let |repeat|if |otherwise|else|end if|end while|end repeat|unless|does the player mean|Persuasion|persuasion|A thing|A room|A person|The )\b/g, '<span class="syn-kw">$1</span>');
  html = html.replace(/\b(\d+)\b/g, '<span class="syn-num">$1</span>');
  return html;
}

/* ==================================================================
   ENGINE-AWARE HIGHLIGHTER DISPATCH
   ================================================================== */
/* ==================================================================
   REZ SYNTAX HIGHLIGHTER
   ================================================================== */
var REZ_ELEMENT_RE = /^@\w+/;

function highlightRez(line) {
  if (REZ_ELEMENT_RE.test(line)) return '<span class="syn-head">' + esc(line) + '</span>';
  if (/^\s*%%/.test(line)) return '<span class="syn-cmt">' + esc(line) + '</span>';

  var out = '', state = 'normal', buf = '';

  function flush(cls) {
    if (!buf) return;
    if (cls) out += '<span class="' + cls + '">' + esc(buf) + '</span>';
    else out += esc(buf);
    buf = '';
  }

  for (var i = 0; i < line.length; i++) {
    var ch = line[i];
    if (state === 'normal') {
      if (ch === '"') { flush(); buf = ch; state = 'string'; }
      else if (ch === '`') { flush(); buf = ch; state = 'template'; }
      else if (ch === '#' && /\w/.test(line[i+1] || '')) { flush(); buf = ch; state = 'ref'; }
      else if (ch === ':' && /\w/.test(line[i+1] || '')) { flush(); buf = ch; state = 'keyword'; }
      else if (ch === '$' && /\w/.test(line[i+1] || '')) { flush(); buf = ch; state = 'global'; }
      else if (ch === '%' && line[i+1] === '%') { flush(); out += '<span class="syn-cmt">' + esc(line.slice(i)) + '</span>'; return out; }
      else buf += ch;
    } else if (state === 'string') {
      buf += ch;
      if (ch === '"') { flush('syn-str'); state = 'normal'; }
    } else if (state === 'template') {
      buf += ch;
      if (ch === '`') { flush('syn-str'); state = 'normal'; }
    } else if (state === 'ref') {
      if (/\w/.test(ch)) buf += ch;
      else { flush('syn-sub'); buf = ch; state = 'normal'; }
    } else if (state === 'keyword') {
      if (/\w/.test(ch)) buf += ch;
      else { flush('syn-kw'); buf = ch; state = 'normal'; }
    } else if (state === 'global') {
      if (/[\w.]/.test(ch)) buf += ch;
      else { flush('syn-num'); buf = ch; state = 'normal'; }
    }
  }
  if (state === 'string' || state === 'template') flush('syn-str');
  else if (state === 'ref') flush('syn-sub');
  else if (state === 'keyword') flush('syn-kw');
  else if (state === 'global') flush('syn-num');
  else flush();

  // Highlight @directives inline
  out = out.replace(/(@\w+)/g, '<span class="syn-head">$1</span>');
  return out;
}

/* ==================================================================
   INK SYNTAX HIGHLIGHTER
   ================================================================== */
var INK_KNOT_RE = /^\s*={2,}\s*(?:function\s+)?([\w()\s,]+?)\s*=*\s*$/;
var INK_STITCH_RE = /^\s*=\s*([\w()\s,]+?)\s*$/;

function highlightInk(line) {
  var trimmed = line.trimStart();
  var indent = esc(line.slice(0, line.length - trimmed.length));
  if (trimmed.startsWith('//')) return indent + '<span class="syn-cmt">' + esc(trimmed) + '</span>';
  if (INK_KNOT_RE.test(line) || INK_STITCH_RE.test(line)) return '<span class="syn-head">' + esc(line) + '</span>';
  if (/^\s*~/.test(line)) return indent + '<span class="syn-num">' + esc(trimmed) + '</span>';
  var html = esc(line);
  html = html.replace(/^(\s*)([*+]+|-+)(\s)/, '$1<span class="syn-kw">$2</span>$3');
  html = html.replace(/-&gt;\s*[\w.]+|&lt;-\s*[\w.]+|\b(END|DONE)\b/g, '<span class="syn-sub">$&</span>');
  html = html.replace(/\{[^}]*\}/g, '<span class="syn-str">$&</span>');
  html = html.replace(/#[^#<]*/g, '<span class="syn-tbl">$&</span>');
  return html;
}

/* ==================================================================
   BASIC SYNTAX HIGHLIGHTER (wwwbasic, applesoft, bwbasic, qbjc)
   ================================================================== */
var BASIC_ENGINES = { wwwbasic: 1, applesoft: 1, bwbasic: 1, qbjc: 1 };
var BASIC_REM_RE = /^\s*\d*\s*(REM\b|')/i;
var BASIC_KEYWORDS = /\b(PRINT|INPUT|IF|THEN|ELSE|ELSEIF|GOTO|GOSUB|RETURN|FOR|TO|STEP|NEXT|LET|DIM|READ|DATA|END|STOP|ON|GET|HOME|CLS|LOCATE|COLOR|POKE|PEEK|CALL|DEF|FN|AND|OR|NOT|XOR|MOD|TAB|LEN|VAL|STR\$|MID\$|LEFT\$|RIGHT\$|CHR\$|ASC|INT|RND|ABS|SGN|SQR|INKEY\$|WHILE|WEND|DO|LOOP|UNTIL|SELECT|CASE|SUB|FUNCTION|DECLARE|SHARED|CONST|TYPE|OPEN|CLOSE|RESTORE|RANDOMIZE|TIMER|SLEEP|WAIT|SWAP|LINE|SCREEN|WIDTH|HTAB|VTAB|INVERSE|NORMAL|FLASH|SPEED|TEXT|GR|HGR|PLOT|HLIN|VLIN|CLEAR|NEW|RUN|USING|WRITE|LPRINT|BEEP|SOUND|PLAY|KEY|IS|EXIT|ERASE|REDIM|OPTION|BASE|STRING\$|SPACE\$|UCASE\$|LCASE\$|INSTR|LTRIM\$|RTRIM\$|HEX\$|CINT|CLNG|CSNG|CDBL|FIX|ATN|COS|SIN|TAN|EXP|LOG|POS|CSRLIN|DEFINT|DEFSTR|DEFSNG|DEFDBL|DEFLNG|RESUME|ERROR|ERR|ERL|SYSTEM|PUT|EOF)\b/gi;

function highlightBasic(line) {
  var m = line.match(/^(\s*)(\d+)(\s*)([\s\S]*)$/);
  var prefix = '', rest = line;
  if (m) {
    prefix = esc(m[1]) + '<span class="syn-num">' + esc(m[2]) + '</span>' + esc(m[3]);
    rest = m[4];
  }
  if (/^\s*(REM\b|')/i.test(rest)) return prefix + '<span class="syn-cmt">' + esc(rest) + '</span>';
  function code(s) { return esc(s).replace(BASIC_KEYWORDS, '<span class="syn-kw">$1</span>'); }
  var out = '', buf = '', i = 0;
  while (i < rest.length) {
    if (rest[i] === '"') {
      out += code(buf); buf = '';
      var j = rest.indexOf('"', i + 1);
      if (j < 0) j = rest.length - 1;
      out += '<span class="syn-str">' + esc(rest.slice(i, j + 1)) + '</span>';
      i = j + 1;
    } else {
      buf += rest[i]; i++;
    }
  }
  return prefix + out + code(buf);
}

/* ==================================================================
   ENGINE-AWARE HIGHLIGHTER DISPATCH
   ================================================================== */
function highlightLine(line, engine) {
  if (engine === 'rez') return highlightRez(line);
  if (engine === 'ink') return highlightInk(line);
  if (BASIC_ENGINES[engine]) return highlightBasic(line);
  return highlightInform(line);
}

function isHeadingLine(line, engine) {
  if (engine === 'rez') return REZ_ELEMENT_RE.test(line);
  if (engine === 'ink') return INK_KNOT_RE.test(line) || INK_STITCH_RE.test(line);
  if (BASIC_ENGINES[engine]) return BASIC_REM_RE.test(line);
  return I7_HEADING.test(line);
}

/* ==================================================================
   SOURCE RENDERER
   ================================================================== */
function renderSource(lines, engine) {
  var rows = [];
  for (var i = 0; i < lines.length; i++) {
    var num = i + 1;
    var cls = isHeadingLine(lines[i], engine) ? ' class="heading-line"' : '';
    rows.push('<tr id="L' + num + '"' + cls + '><td class="ln">' + num + '</td><td class="lc">' + highlightLine(lines[i], engine) + '</td></tr>');
  }
  document.getElementById('source-main').innerHTML = '<table class="code">' + rows.join('') + '</table>';
}

/* ==================================================================
   NAVIGATION SIDEBAR
   ================================================================== */
function buildNav(lines, engine) {
  var nav = document.getElementById('nav');
  var items = [];

  if (engine === 'rez') {
    for (var i = 0; i < lines.length; i++) {
      var rm = lines[i].match(/^@(\w+)\s+(.*)/);
      if (!rm) continue;
      var num = i + 1;
      var tag = rm[1];
      var rest = rm[2].replace(/\s*\{.*/, '').trim();
      var cls = 'nav-item';
      if (tag === 'game' || tag === 'scene') cls += ' nav-part';
      else cls += ' nav-chapter';
      items.push('<a class="' + cls + '" data-line="' + num + '">' + esc('@' + tag + ' ' + rest) + '</a>');
    }
  } else if (engine === 'ink') {
    for (var i = 0; i < lines.length; i++) {
      var km = lines[i].match(INK_KNOT_RE);
      if (km) { items.push('<a class="nav-item nav-part" data-line="' + (i + 1) + '">' + esc(km[1].trim()) + '</a>'); continue; }
      var sm = lines[i].match(INK_STITCH_RE);
      if (sm) items.push('<a class="nav-item nav-chapter" data-line="' + (i + 1) + '">' + esc(sm[1].trim()) + '</a>');
    }
  } else if (BASIC_ENGINES[engine]) {
    for (var i = 0; i < lines.length; i++) {
      var bm = lines[i].match(/^\s*\d*\s*(?:REM\b|')\s*(.*)$/i);
      if (bm && bm[1].trim()) items.push('<a class="nav-item nav-section" data-line="' + (i + 1) + '">' + esc(bm[1].trim().slice(0, 60)) + '</a>');
    }
  } else {
    for (var i = 0; i < lines.length; i++) {
      var hm = lines[i].match(I7_HEADING);
      if (!hm) continue;
      var num = i + 1;
      var lvl = hm[1].toLowerCase();
      var cls = 'nav-item';
      if (lvl === 'volume' || lvl === 'book' || lvl === 'part') cls += ' nav-part';
      else if (lvl === 'chapter') cls += ' nav-chapter';
      else cls += ' nav-section';
      items.push('<a class="' + cls + '" data-line="' + num + '">' + esc(lines[i]) + '</a>');
    }
  }

  nav.innerHTML = items.join('');

  nav.addEventListener('click', function(e) {
    var a = e.target.closest('.nav-item');
    if (!a) return;
    nav.querySelectorAll('.nav-item').forEach(function(el) { el.classList.remove('active'); });
    a.classList.add('active');
    var row = document.getElementById('L' + a.dataset.line);
    if (row) row.scrollIntoView({ block: 'start' });
  });
}

/* ==================================================================
   SEARCH
   ================================================================== */
function initSearch() {
  var input = document.getElementById('search-source');
  var wrap = document.getElementById('source-main');
  var hits = [], cur = -1, debounce;

  function clearHits() {
    wrap.querySelectorAll('.search-hit').forEach(function(el) { el.outerHTML = el.textContent; });
    hits = []; cur = -1;
  }

  function doSearch(q) {
    clearHits();
    if (!q || q.length < CONFIG.SEARCH_MIN_LENGTH) return;
    var lower = q.toLowerCase();
    wrap.querySelectorAll('td.lc').forEach(function(td) {
      if (td.textContent.toLowerCase().includes(lower)) markMatches(td, q);
    });
    hits = Array.from(wrap.querySelectorAll('.search-hit'));
    if (hits.length) {
      cur = 0;
      hits[0].classList.add('search-current');
      hits[0].scrollIntoView({ block: 'center' });
    }
  }

  function markMatches(el, q) {
    var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    var nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    var lower = q.toLowerCase();
    nodes.forEach(function(node) {
      var text = node.textContent, idx = text.toLowerCase().indexOf(lower);
      if (idx === -1) return;
      var span = document.createElement('span');
      span.className = 'search-hit';
      span.textContent = text.slice(idx, idx + q.length);
      var parent = node.parentNode;
      if (idx > 0) parent.insertBefore(document.createTextNode(text.slice(0, idx)), node);
      parent.insertBefore(span, node);
      var after = text.slice(idx + q.length);
      if (after) parent.insertBefore(document.createTextNode(after), node);
      parent.removeChild(node);
    });
  }

  function next() {
    if (!hits.length) return;
    hits[cur].classList.remove('search-current');
    cur = (cur + 1) % hits.length;
    hits[cur].classList.add('search-current');
    hits[cur].scrollIntoView({ block: 'center' });
  }

  function prev() {
    if (!hits.length) return;
    hits[cur].classList.remove('search-current');
    cur = (cur - 1 + hits.length) % hits.length;
    hits[cur].classList.add('search-current');
    hits[cur].scrollIntoView({ block: 'center' });
  }

  input.addEventListener('input', function() {
    clearTimeout(debounce);
    var self = this;
    debounce = setTimeout(function() { doSearch(self.value); }, CONFIG.SEARCH_DEBOUNCE_MS);
  });

  input.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') { e.preventDefault(); e.shiftKey ? prev() : next(); }
    if (e.key === 'Escape') { clearHits(); this.value = ''; this.blur(); }
  });
}

/* ==================================================================
   DISPLAY SOURCE — render + nav + search + line count
   ================================================================== */
function displaySource(text, engine) {
  var lines = text.replace(/\r\n?/g, '\n').replace(/^\n/, '').replace(/\n$/, '').split('\n');
  renderSource(lines, engine);
  buildNav(lines, engine);
  initSearch();
  document.getElementById('line-count').textContent = lines.length + ' lines';
  document.getElementById('search-source').value = '';
  updateSidebarToggle();
}

/* ==================================================================
   SIDEBAR TOGGLE — show/hide outline panel
   ================================================================== */
function updateSidebarToggle() {
  var sidebar = document.getElementById('nav-sidebar');
  var toggleBtn = document.getElementById('sidebar-toggle');
  // Reset sidebar state when switching games
  sidebar.classList.remove('collapsed', 'sidebar-open');
  var isNarrow = window.matchMedia('(max-width: 1024px)').matches;
  toggleBtn.innerHTML = isNarrow ? '&#9654;' : '&#9664;';
}

(function() {
  var toggleBtn = document.getElementById('sidebar-toggle');
  toggleBtn.addEventListener('click', function() {
    var sidebar = document.getElementById('nav-sidebar');
    var isNarrow = window.matchMedia('(max-width: 1024px)').matches;
    if (isNarrow) {
      var open = sidebar.classList.toggle('sidebar-open');
      toggleBtn.innerHTML = open ? '&#9664;' : '&#9654;';
    } else {
      var collapsed = sidebar.classList.toggle('collapsed');
      toggleBtn.innerHTML = collapsed ? '&#9654;' : '&#9664;';
    }
  });
})();

/* ==================================================================
   SOURCE PANE MODE — single function drives all visibility via CSS
   ================================================================== */
function setSourcePaneMode(mode) {
  // mode: "inline", "browser", "walkthrough", "tests"
  document.getElementById('source-pane').dataset.sourceMode = mode;
}

/* ==================================================================
   LOAD SOURCE FOR GAME — fetch with cache
   ================================================================== */
function loadSourceForGame(gameId) {
  var g = gameMap[gameId];
  if (!g) return;

  var browserFrame = document.getElementById('source-browser-frame');
  document.getElementById('source-filepath').textContent = g.sourceLabel || (g.sourceUrl || '').split('/').pop() || g.id;

  if (g.sourceBrowser) {
    setSourcePaneMode('browser');
    browserFrame.src = g.sourceUrl;
    browserFrame.onload = function() { themeIframe(browserFrame); };
    document.getElementById('line-count').textContent = '';
    return;
  }

  setSourcePaneMode('inline');
  browserFrame.src = 'about:blank';

  if (sourceCache[gameId]) {
    displaySource(sourceCache[gameId], g.engine);
    return;
  }

  document.getElementById('source-main').innerHTML = '<div style="padding:20px;color:#605840;font-style:italic;">Loading source\u2026</div>';
  document.getElementById('line-count').textContent = '';
  fetch(g.sourceUrl)
    .then(function(r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.text();
    })
    .then(function(text) {
      sourceCache[gameId] = text;
      if (currentGame === gameId) displaySource(text, g.engine);
    })
    .catch(function() {
      if (currentGame === gameId) {
        document.getElementById('source-main').innerHTML = '<div style="padding:20px;color:#806050;">Source unavailable.</div>';
      }
    });
}

/* ==================================================================
   VIEW SWITCHING — source / walkthrough tabs
   ================================================================== */
/* ------ Toggle-button helpers ------ */

function isToggleActive(pane) {
  var btn = document.querySelector('.view-toggle[data-pane="' + pane + '"]');
  return btn ? btn.classList.contains('active') : false;
}

function setToggleActive(pane, on) {
  var btn = document.querySelector('.view-toggle[data-pane="' + pane + '"]');
  if (btn) btn.classList.toggle('active', !!on);
}

function getActiveSidePane() {
  var sides = ['source', 'walkthrough', 'tests'];
  for (var i = 0; i < sides.length; i++) {
    if (isToggleActive(sides[i])) return sides[i];
  }
  return null;
}

function getViewMode() {
  var parts = [];
  if (isToggleActive('game')) parts.push('game');
  var side = getActiveSidePane();
  if (side) parts.push(side);
  return parts.join('+') || 'game';
}

function handleToggleClick(pane) {
  var wasActive = isToggleActive(pane);

  if (pane === 'game') {
    if (wasActive) {
      // Turning off game — need at least one side pane
      if (!getActiveSidePane()) setToggleActive('source', true);
    }
    setToggleActive('game', !wasActive);
  } else {
    // Side panes are radio: clicking one deactivates the others
    if (wasActive) {
      // Turning off the active side pane — game must stay on
      if (!isToggleActive('game')) return; // can't leave everything off
      setToggleActive(pane, false);
    } else {
      ['source', 'walkthrough', 'tests'].forEach(function(p) {
        setToggleActive(p, p === pane);
      });
    }
  }

  applyView(getViewMode());
}

function applyView(mode) {
  // mode: "game+source", "game+walkthrough", "game+tests", "game",
  //       "source", "walkthrough", "tests"
  // Normalize: URLSearchParams decodes + as space; treat both as delimiter
  mode = mode.replace(/\s+/g, '+');
  var parts = mode.split('+');
  var showGame = parts.indexOf('game') !== -1;
  var sidePane = null;
  if (parts.indexOf('tests') !== -1) sidePane = 'tests';
  if (parts.indexOf('walkthrough') !== -1) sidePane = 'walkthrough';
  if (parts.indexOf('source') !== -1) sidePane = 'source';

  // Sync toggle states to match the mode string
  setToggleActive('game', showGame);
  setToggleActive('source', sidePane === 'source');
  setToggleActive('walkthrough', sidePane === 'walkthrough');
  setToggleActive('tests', sidePane === 'tests');

  // Apply CSS
  document.body.classList.toggle('source-collapsed', !sidePane);
  document.body.classList.toggle('game-collapsed', !showGame);

  // Set source pane content mode
  if (sidePane === 'walkthrough') {
    setSourcePaneMode('walkthrough');
  } else if (sidePane === 'tests') {
    setSourcePaneMode('tests');
  } else if (sidePane) {
    var g = gameMap[currentGame];
    setSourcePaneMode(g && g.sourceBrowser ? 'browser' : 'inline');
  }

  currentView = sidePane || 'source';

  // Update URL
  var params = new URLSearchParams(window.location.search);
  if (mode !== 'game') {
    params.set('view', mode);
  } else {
    params.delete('view');
  }
  history.replaceState(null, '', '?' + params.toString());
}

/* ==================================================================
   LOAD WALKTHROUGH FOR GAME — stub
   ================================================================== */
function loadWalkthroughForGame(gameId) {
  var g = gameMap[gameId];
  var frame = document.getElementById('walkthrough-frame');
  var msg = document.getElementById('walkthrough-unavailable');
  var status = document.getElementById('wt-status');

  if (g && g.walkthroughUrl) {
    // The hub renders walkthroughs itself; the game only ships the raw txt files.
    frame.src = 'walkthrough.html?game=' + encodeURIComponent(gameId);
    frame.style.display = '';
    msg.style.display = 'none';
    status.textContent = '';
    frame.onload = function() { themeIframe(frame); };
  } else {
    frame.src = 'about:blank';
    frame.style.display = 'none';
    msg.style.display = '';
    status.textContent = 'Not available';
  }
}

/* ==================================================================
   LOAD TESTS FOR GAME
   ================================================================== */
function loadTestsForGame(gameId) {
  var g = gameMap[gameId];
  var frame = document.getElementById('tests-frame');
  var msg = document.getElementById('tests-unavailable');
  var testsBtn = document.querySelector('.view-toggle[data-pane="tests"]');

  if (g && g.testsUrl) {
    frame.src = g.testsUrl;
    frame.style.display = '';
    msg.style.display = 'none';
    frame.onload = function() { themeTestsIframe(); };
    if (testsBtn) testsBtn.style.display = '';
  } else {
    frame.src = 'about:blank';
    frame.style.display = 'none';
    msg.style.display = '';
    if (testsBtn) testsBtn.style.display = 'none';
    // If tests was the active side pane, fall back to source
    if (isToggleActive('tests')) {
      setToggleActive('tests', false);
      setToggleActive('source', true);
    }
  }
}

/* ==================================================================
   SOUND CONTROLS
   ================================================================== */
var soundReady = false;

function initSoundControls() {
  var controls = document.getElementById('sound-controls');
  var muteBtn = document.getElementById('mute-btn');
  var slider = document.getElementById('volume-slider');

  // Restore persisted state
  var savedMuted = localStorage.getItem('ifhub-audio-muted');
  var savedVolume = localStorage.getItem('ifhub-audio-volume');
  var isMuted = savedMuted === '1';
  var volume = savedVolume !== null ? parseInt(savedVolume, 10) : CONFIG.DEFAULT_VOLUME;

  slider.value = volume;
  muteBtn.classList.toggle('muted', isMuted);

  muteBtn.addEventListener('click', function () {
    isMuted = !isMuted;
    localStorage.setItem('ifhub-audio-muted', isMuted ? '1' : '0');
    muteBtn.classList.toggle('muted', isMuted);
    sendGameMessage({ type: 'ifhub:setMute', muted: isMuted });
  });

  slider.addEventListener('input', function () {
    volume = parseInt(this.value, 10);
    localStorage.setItem('ifhub-audio-volume', volume);
    sendGameMessage({ type: 'ifhub:setVolume', volume: volume / 100 });
  });

  // Listen for soundReady from iframe
  window.addEventListener('message', function (e) {
    if (!e.data || e.data.type !== 'ifhub:soundReady') return;
    soundReady = true;
    controls.style.display = '';
    // Push current state to iframe
    sendGameMessage({ type: 'ifhub:setMute', muted: isMuted });
    sendGameMessage({ type: 'ifhub:setVolume', volume: volume / 100 });
  });
}

function sendGameMessage(msg) {
  var iframe = document.getElementById('game-frame');
  if (iframe && iframe.contentWindow) {
    iframe.contentWindow.postMessage(msg, '*');
  }
}

/* ==================================================================
   STYLE DROPDOWN (overlay-aware theme selector)
   ================================================================== */
function getStylePref() {
  var params = new URLSearchParams(window.location.search);
  return params.get('theme') || null;
}

function setStylePref(gameId, val) {
  var params = new URLSearchParams(window.location.search);
  if (val && val !== 'classic') {
    params.set('theme', val);
  } else {
    params.delete('theme');
  }
  history.replaceState(null, '', '?' + params.toString());
}

function buildStyleDropdown(gameId) {
  var container = document.getElementById('theme-picker');
  if (!container) return;
  container.innerHTML = '';

  var select = document.createElement('select');
  select.id = 'style-select';
  select.title = 'Theme';
  select.style.cssText = THEME_SELECT_STYLE;

  var g = gameId ? gameMap[gameId] : null;
  var hasOverlay = g && g.overlayLabel;

  // If game has an overlay, add it as first option
  if (hasOverlay) {
    var overlayOpt = document.createElement('option');
    overlayOpt.value = 'overlay';
    overlayOpt.textContent = g.overlayLabel;
    select.appendChild(overlayOpt);

    // Separator
    var sep = document.createElement('option');
    sep.disabled = true;
    sep.textContent = '\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500';
    select.appendChild(sep);
  }

  // Platform themes
  populateThemeOptions(select);

  // Determine current selection:
  // Overlay games always default to their own overlay — URL theme is ignored for them
  // but kept in URL so switching to a non-overlay game applies it.
  var stored = getStylePref();
  if (hasOverlay) {
    // Overlay games: always use overlay unless user explicitly picked a theme for this game
    select.value = 'overlay';
  } else if (stored) {
    select.value = stored;
  } else {
    select.value = getThemeId();
  }

  select.addEventListener('change', function() {
    var val = this.value;
    if (gameId) setStylePref(gameId, val);

    var gEntry = gameId ? gameMap[gameId] : null;
    var hasOverlay = gEntry && gEntry.overlayLabel;

    if (val === 'overlay' || val === 'classic') {
      // Classic = game's native look; overlay = game's native overlay
      var classic = getTheme('classic');
      applyChrome(classic);
      if (hasOverlay) {
        sendGameMessage({ type: 'ifhub:restoreOverlay' });
      } else {
        // Non-overlay: remove any injected theme
        var gf = document.getElementById('game-frame');
        if (gf) removeThemeCSS(gf);
      }
    } else {
      // Apply platform theme to chrome and game
      var theme = getTheme(val);
      setThemeId(val);
      applyChrome(theme);
      if (hasOverlay) {
        sendGameMessage({
          type: 'ifhub:applyTheme',
          game: theme.game,
          scrollbar: theme.scrollbar
        });
      }
      // themeAllIframes handles direct injection for non-overlay games
    }
    themeAllIframes();
  });

  container.appendChild(select);

  // Apply current selection
  if (gameId) applyCurrentStyle(gameId, select.value);
}

function applyCurrentStyle(gameId, val) {
  var gEntry = gameId ? gameMap[gameId] : null;
  var hasOverlay = gEntry && gEntry.overlayLabel;

  if (val === 'overlay' || val === 'classic') {
    // Classic = game's native look (no override); overlay = game's native overlay
    var classic = getTheme('classic');
    applyChrome(classic);
    if (hasOverlay) {
      setTimeout(function() { sendGameMessage({ type: 'ifhub:restoreOverlay' }); }, CONFIG.IFRAME_THEME_DELAY_MS);
    } else {
      setTimeout(function() {
        var gf = document.getElementById('game-frame');
        if (gf) removeThemeCSS(gf);
      }, CONFIG.IFRAME_THEME_DELAY_MS);
    }
  } else {
    var theme = getTheme(val);
    applyChrome(theme);
    if (hasOverlay) {
      setTimeout(function() {
        sendGameMessage({
          type: 'ifhub:applyTheme',
          game: theme.game,
          scrollbar: theme.scrollbar
        });
      }, CONFIG.IFRAME_THEME_DELAY_MS);
    }
    // themeAllIframes handles direct injection for non-overlay games
  }
  setTimeout(function() { themeAllIframes(); }, CONFIG.IFRAME_THEME_DELAY_MS);
}

/* ==================================================================
   THEME IFRAMES (source browser, walkthrough, game)
   ================================================================== */

function injectThemeCSS(iframe, css) {
  try {
    var doc = iframe.contentDocument || (iframe.contentWindow && iframe.contentWindow.document);
    if (!doc || !doc.head) return;
    var existing = doc.getElementById('ifhub-theme-override');
    if (existing) existing.remove();
    if (!css) return;
    ensureRetroFonts(doc);
    var style = doc.createElement('style');
    style.id = 'ifhub-theme-override';
    style.textContent = css;
    doc.head.appendChild(style);
  } catch(e) { /* cross-origin — can't inject */ }
}

function removeThemeCSS(iframe) {
  try {
    var doc = iframe.contentDocument || (iframe.contentWindow && iframe.contentWindow.document);
    if (!doc || !doc.head) return;
    var existing = doc.getElementById('ifhub-theme-override');
    if (existing) existing.remove();
  } catch(e) {}
}

// Theme a document-style iframe (source, walkthrough)
function themeIframe(iframe) {
  if (!iframe || !iframe.src || iframe.src === 'about:blank') return;
  var themeId = getThemeId();
  if (themeId === 'classic') { removeThemeCSS(iframe); return; }
  var theme = getTheme(themeId);
  injectThemeCSS(iframe, buildChromeCSS(theme.chrome, theme.scrollbar));
}

// Theme the tests iframe (ifplayer report) — always injects because
// ifplayer defaults to a light theme while IF Hub is dark
function themeTestsIframe() {
  var iframe = document.getElementById('tests-frame');
  if (!iframe || !iframe.src || iframe.src === 'about:blank') return;
  var theme = getTheme(getThemeId());
  injectThemeCSS(iframe, buildTestReportCSS(theme.chrome, theme.scrollbar));
}

// Theme the game iframe (direct injection + postMessage fallback)
function themeGameIframe() {
  var iframe = document.getElementById('game-frame');
  if (!iframe || !iframe.src || iframe.src === 'about:blank') return;

  // Games with overlays use postMessage only — don't override
  var g = currentGame ? gameMap[currentGame] : null;
  if (g && g.overlayLabel) return;

  var sel = document.getElementById('style-select');
  var val = sel ? sel.value : getThemeId();
  if (val === 'overlay' || val === 'classic') {
    removeThemeCSS(iframe);
    sendGameMessage({ type: 'ifhub:restoreOverlay' });
    return;
  }

  var theme = getTheme(val);
  var engine = g ? (g.engine || '') : '';
  var css;
  if (engine === 'ink') {
    css = buildInkCSS(theme.game, theme.scrollbar);
  } else if (engine === 'basic') {
    css = buildBasicCSS(theme.game, theme.scrollbar);
  } else if (engine === 'rez') {
    css = buildRezCSS(theme.game, theme.scrollbar);
  } else {
    // inform7, zmachine, or unknown — Parchment rules
    css = buildParchmentCSS(theme.game, theme.scrollbar);
  }
  // Try direct injection (same-origin); also send postMessage (cross-origin fallback)
  injectThemeCSS(iframe, css);
  sendGameMessage({ type: 'ifhub:applyTheme', game: theme.game, scrollbar: theme.scrollbar });
  try { iframe.contentWindow.dispatchEvent(new Event('resize')); } catch(e) {}
}

function themeAllIframes() {
  ['source-browser-frame', 'walkthrough-frame'].forEach(function(id) {
    var iframe = document.getElementById(id);
    if (iframe) themeIframe(iframe);
  });
  themeTestsIframe();
  themeGameIframe();
}

/* ==================================================================
   SWITCH GAME
   ================================================================== */
function switchGame(gameId) {
  var g = gameMap[gameId];
  if (!g) return;

  currentGame = gameId;

  // Keep current view when switching games
  var currentViewMode = getViewMode();

  // Hide sound controls until iframe reports ready
  soundReady = false;
  document.getElementById('sound-controls').style.display = 'none';

  // Update dropdown
  document.getElementById('game-select').value = gameId;

  // Load game's own play page via URL
  var iframe = document.getElementById('game-frame');
  iframe.src = g.playUrl;
  iframe.title = g.title + ' \u2014 Interactive Fiction';

  // Update page title
  document.title = g.title + ' \u2014 Source & Game';

  // Update hamburger landing page link
  var landingLink = document.getElementById('game-landing-link');
  if (g.landingUrl) {
    landingLink.href = g.landingUrl;
    landingLink.textContent = g.title + ' Page';
    landingLink.style.display = '';
  } else {
    landingLink.style.display = 'none';
  }

  // Rebuild style dropdown for this game
  buildStyleDropdown(gameId);

  // Re-apply style after iframe loads
  iframe.onload = function() {
    var sel = document.getElementById('style-select');
    if (sel && sel.value !== 'overlay' && sel.value !== 'classic') {
      if (g && g.overlayLabel) {
        var theme = getTheme(sel.value);
        sendGameMessage({
          type: 'ifhub:applyTheme',
          game: theme.game,
          scrollbar: theme.scrollbar
        });
      } else {
        themeGameIframe();
      }
    }
  };

  // Load source, walkthrough, and tests, then re-apply the current view.
  // loadTestsForGame may hide the tests toggle and fall back to source,
  // so read the view mode AFTER it runs to pick up any corrections.
  loadSourceForGame(gameId);
  loadWalkthroughForGame(gameId);
  loadTestsForGame(gameId);
  applyView(getViewMode());
}
