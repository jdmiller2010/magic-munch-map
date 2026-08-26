/* Magic Munch Map service worker.

   The job here is a park with no usable signal. Three rules:

   1. Never intercept anything live. Firestore, Firebase auth and the Disney
      endpoints go straight to the network - caching a long-poll or an auth
      handshake breaks sync in ways that are miserable to debug.
   2. Navigations are network-first, so a deploy is picked up on the next load
      instead of the app pinning itself to a stale build forever.
   3. Map tiles are cached only as you browse them. OpenStreetMap's tile policy
      forbids bulk prefetching, so nothing is ever fetched ahead of time.
*/

var VERSION = "mmm-v1";
var SHELL   = VERSION + "-shell";
var ASSETS  = VERSION + "-assets";
var TILES   = VERSION + "-tiles";
var TILE_CAP = 700;

// dining.js is over a megabyte, so it is fetched on first use rather than
// blocking the install.
var PRECACHE = ["./", "./index.html", "./manifest.webmanifest",
                "./icons/icon-192.png", "./icons/apple-touch-icon.png"];

var PASSTHROUGH = [
  "firestore.googleapis.com", "identitytoolkit.googleapis.com",
  "securetoken.googleapis.com", "firebaseinstallations.googleapis.com",
  "firebaseapp.com", "google.com", "googleapis.com",
  "disneyland.disney.go.com", "overpass-api.de", "overpass.kumi.systems",
  "nominatim.openstreetmap.org"
];

self.addEventListener("install", function(e){
  e.waitUntil(
    caches.open(SHELL)
      .then(function(c){ return c.addAll(PRECACHE); })
      .then(function(){ return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function(e){
  e.waitUntil(
    caches.keys().then(function(keys){
      return Promise.all(keys.map(function(k){
        if(k.indexOf(VERSION) !== 0) return caches.delete(k);
      }));
    }).then(function(){ return self.clients.claim(); })
  );
});

function trimCache(name, max){
  return caches.open(name).then(function(c){
    return c.keys().then(function(keys){
      if(keys.length <= max) return;
      return Promise.all(keys.slice(0, keys.length - max).map(function(k){ return c.delete(k); }));
    });
  });
}

function cacheFirst(req, cacheName, cap){
  return caches.open(cacheName).then(function(c){
    return c.match(req).then(function(hit){
      if(hit) return hit;
      return fetch(req).then(function(res){
        // Opaque cross-origin responses still cache and still replay offline.
        if(res && (res.ok || res.type === "opaque")){
          c.put(req, res.clone());
          if(cap) trimCache(cacheName, cap);
        }
        return res;
      });
    });
  });
}

self.addEventListener("fetch", function(e){
  var req = e.request;
  if(req.method !== "GET") return;

  var url;
  try{ url = new URL(req.url); }catch(err){ return; }
  if(url.protocol !== "http:" && url.protocol !== "https:") return;

  for(var i = 0; i < PASSTHROUGH.length; i++){
    if(url.hostname.indexOf(PASSTHROUGH[i]) !== -1) return;
  }

  if(url.hostname.indexOf("tile.openstreetmap.org") !== -1){
    e.respondWith(cacheFirst(req, TILES, TILE_CAP));
    return;
  }

  // Fonts, Leaflet, the Firebase SDK, Disney's photo CDN: versioned or stable,
  // so serve from cache and skip the network entirely once seen.
  if(url.origin !== self.location.origin){
    e.respondWith(cacheFirst(req, ASSETS));
    return;
  }

  if(req.mode === "navigate"){
    e.respondWith(
      fetch(req).then(function(res){
        var copy = res.clone();
        caches.open(SHELL).then(function(c){ c.put("./index.html", copy); });
        return res;
      }).catch(function(){
        return caches.match("./index.html").then(function(hit){
          return hit || caches.match("./");
        });
      })
    );
    return;
  }

  // Same-origin data and code: serve what we have, refresh in the background.
  e.respondWith(
    caches.open(ASSETS).then(function(c){
      return c.match(req).then(function(hit){
        var net = fetch(req).then(function(res){
          if(res && res.ok) c.put(req, res.clone());
          return res;
        }).catch(function(){ return hit; });
        return hit || net;
      });
    })
  );
});
