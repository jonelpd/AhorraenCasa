(function(){
  const clientId = window.AHORRA_ADSENSE_CLIENT_ID || "";
  if (!/^ca-pub-\\d{10,20}$/.test(clientId)) return;
  const script = document.createElement("script");
  script.async = true;
  script.src = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=" + encodeURIComponent(clientId);
  script.crossOrigin = "anonymous";
  document.head.appendChild(script);
  document.querySelectorAll(".ad-slot[data-ad-slot]").forEach(slot => {
    slot.replaceChildren();
    const ins = document.createElement("ins");
    ins.className = "adsbygoogle";
    ins.style.display = "block";
    ins.setAttribute("data-ad-client", clientId);
    ins.setAttribute("data-ad-slot", slot.dataset.adSlot);
    ins.setAttribute("data-ad-format", "auto");
    ins.setAttribute("data-full-width-responsive", "true");
    slot.appendChild(ins);
    try { (window.adsbygoogle = window.adsbygoogle || []).push({}); } catch(e) {}
  });
})();
