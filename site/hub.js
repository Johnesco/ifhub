/* IF Hub — shared data loading and collection filtering for index.html and app.html.
   Load after themes.js. */

/* The collection selected by ?hub=<id>, or null for everything. */
function resolveHub(hubs) {
    var params = new URLSearchParams(window.location.search);
    var hubParam = params.get('hub');
    var activeHub = null;
    if (hubParam) {
        for (var i = 0; i < hubs.length; i++) {
            if (hubs[i].id === hubParam) { activeHub = hubs[i]; break; }
        }
    }
    return { activeHub: activeHub, hubParam: hubParam };
}

/* Does a games.json / cards.json entry belong to a collection? (engine and tag are ANDed) */
function matchesHub(entry, hub) {
    if (!hub || !hub.filter) return true;
    if (hub.filter.engine && entry.engine !== hub.filter.engine) return false;
    if (hub.filter.tag && (!entry.tags || entry.tags.indexOf(hub.filter.tag) === -1)) return false;
    return true;
}

function fetchJson(url) {
    return fetch(url).then(function(r) {
        if (!r.ok) throw new Error(url + ' returned HTTP ' + r.status);
        return r.json().catch(function() { throw new Error(url + ' is not valid JSON'); });
    }, function() {
        throw new Error(url + ' could not be fetched');
    });
}

/* Load the registry file a page needs (games.json or cards.json) together with hubs.json.
   Resolves to { entries, hubs }; rejects with an Error that names the file that failed. */
function loadHubData(dataFile) {
    return Promise.all([fetchJson(dataFile), fetchJson('hubs.json')]).then(function(res) {
        return { entries: res[0], hubs: res[1] };
    });
}

/* Say so when the data did not load, instead of leaving an empty page. */
function showLoadError(containerId, err) {
    var el = containerId ? document.getElementById(containerId) : null;
    var box = document.createElement('div');
    box.className = 'load-error';
    box.setAttribute('role', 'alert');
    box.style.cssText = 'margin:1em;padding:0.8em 1em;border:1px solid var(--border, #553f2a);' +
        'background:var(--card-bg, #1a1410);color:var(--fg, #d4c5a9);font-family:inherit;';
    box.textContent = 'IF Hub could not load its data: ' + (err && err.message ? err.message : String(err)) +
        '. Reload the page; if it keeps failing, the site deploy is broken.';
    if (el) { el.innerHTML = ''; el.appendChild(box); }
    else { document.body.insertBefore(box, document.body.firstChild); }
    if (window.console) console.error(err);
}
