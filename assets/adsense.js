(function(){
  const clientId = window.AHORRA_ADSENSE_CLIENT_ID || "";
  if (/^ca-pub-\d{10,20}$/.test(clientId)) {
    const script = document.createElement("script");
    script.async = true;
    script.src = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=" + encodeURIComponent(clientId);
    script.crossOrigin = "anonymous";
    document.head.appendChild(script);
  }
  const config = document.createElement("script");
  config.src = "assets/analytics-config.js";
  document.head.appendChild(config);
  const analytics = document.createElement("script");
  analytics.src = "assets/analytics.js";
  document.head.appendChild(analytics);
})();