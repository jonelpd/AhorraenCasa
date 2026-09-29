(function(){
  const clientId = window.AHORRA_ADSENSE_CLIENT_ID || "";
  if (!/^ca-pub-\d{10,20}$/.test(clientId)) return;
  const script = document.createElement("script");
  script.async = true;
  script.src = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=" + encodeURIComponent(clientId);
  script.crossOrigin = "anonymous";
  document.head.appendChild(script);
})();
