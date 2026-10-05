const V="hub-fe6dc5f8dc";
const FILES=["./", "manifest.json", "icon-192.png", "apple-touch-icon.png", "shots/0.jpg", "shots/1.jpg", "shots/10.jpg", "shots/11.jpg", "shots/12.jpg", "shots/13.jpg", "shots/14.jpg", "shots/15.jpg", "shots/16.jpg", "shots/17.jpg", "shots/2.jpg", "shots/3.jpg", "shots/4.jpg", "shots/5.jpg", "shots/6.jpg", "shots/7.jpg", "shots/8.jpg", "shots/9.jpg"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(FILES).catch(()=>{})).then(()=>self.skipWaiting()))});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==V).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener("fetch",e=>{
  const r=e.request;if(r.method!=="GET")return;
  const u=new URL(r.url);if(u.origin!==location.origin)return;
  if(u.pathname.endsWith("status.json")){
    e.respondWith(fetch(r).then(x=>{const c=x.clone();caches.open(V).then(ca=>ca.put(r,c));return x}).catch(()=>caches.match(r)));return}
  e.respondWith(caches.open(V).then(ca=>ca.match(r,{ignoreSearch:true}).then(hit=>{
    const net=fetch(r).then(x=>{if(x.ok)ca.put(r,x.clone());return x}).catch(()=>hit);
    return hit||net})));
});
