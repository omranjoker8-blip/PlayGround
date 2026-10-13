/* ARAB STORE service worker: Web Push + offline cache */
const CACHE = "arab-store-v2";
const CORE = ["/store.html", "/products.html", "/product.html", "/cart.html", "/css/style.css", "/js/app.js"];
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(CORE).catch(() => {})).then(() => self.skipWaiting())
  );
});
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET" || !url.pathname.startsWith("/") || url.pathname.startsWith("/api/")) return;
  event.respondWith(
    caches.match(event.request).then((hit) =>
      hit || fetch(event.request).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(event.request, copy).catch(() => {}));
        return res;
      }).catch(() => caches.match("/store.html"))
    )
  );
});
self.addEventListener("push", (event) => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch (_) {}
  const title = data.title || "إشعار جديد";
  const options = {
    body: data.message || "لديك تحديث جديد في المتجر",
    icon: "/site-icon",
    badge: "/site-icon",
    tag: "arab-store-notification",
    renotify: true,
    data: { url: "/activity.html" },
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const target = (event.notification.data && event.notification.data.url) || "/activity.html";
  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((list) => {
      for (const client of list) {
        if ("focus" in client) return client.focus();
      }
      return clients.openWindow(target);
    })
  );
});
