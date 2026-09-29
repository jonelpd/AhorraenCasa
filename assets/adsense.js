(function(){
  const clientId = window.AHORRA_ADSENSE_CLIENT_ID || "";
  if (/^ca-pub-\d{10,20}$/.test(clientId)) {
    const script = document.createElement("script");
    script.async = true;
    script.src = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=" + encodeURIComponent(clientId);
    script.crossOrigin = "anonymous";
    document.head.appendChild(script);
  }
  const source = document.currentScript && document.currentScript.src;
  if (!source) return;
  const config = document.createElement("script");
  config.src = new URL("analytics-config.js", source).href;
  document.head.appendChild(config);
  const analytics = document.createElement("script");
  analytics.src = new URL("analytics.js", source).href;
  document.head.appendChild(analytics);
})();