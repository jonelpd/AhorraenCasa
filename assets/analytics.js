(function(){
  "use strict";
  var id=window.AHORRA_ANALYTICS_ID||"";
  if(!/^G-[A-Z0-9]+$/i.test(id)) return;
  if(window.__AHORRA_ANALYTICS_LOADED) return;
  window.__AHORRA_ANALYTICS_LOADED=true;
  window.dataLayer=window.dataLayer||[];
  window.gtag=function(){window.dataLayer.push(arguments);};
  gtag("js",new Date());
  gtag("config",id,{anonymize_ip:true,transport_type:"beacon"});
  var s=document.createElement("script");s.async=true;s.src="https://www.googletagmanager.com/gtag/js?id="+encodeURIComponent(id);document.head.appendChild(s);
  function send(name,params){try{gtag("event",name,params||{});}catch(e){}}
  send("page_view",{page_location:location.href,page_title:document.title});
  var started=Date.now(),readSent=false;
  function read(){if(readSent)return;readSent=true;send("content_read",{engaged_seconds:Math.round((Date.now()-started)/1000),page_path:location.pathname});}
  setTimeout(read,30000);
  document.addEventListener("visibilitychange",function(){if(document.visibilityState==="hidden")read();});
  document.addEventListener("click",function(e){
    var a=e.target.closest&&e.target.closest("a");if(!a)return;
    var href=a.href||"";
    if(/amazon\./i.test(href)) send("affiliate_click",{affiliate:"amazon",destination:href.slice(0,300),link_text:(a.textContent||"").trim().slice(0,120),page_path:location.pathname});
    var lang=a.getAttribute("hreflang")||a.dataset.lang;
    if(lang) send("language_select",{language:lang});
  },true);
  document.addEventListener("submit",function(e){var f=e.target;if(f&&f.matches&&f.matches("form"))send("form_submit",{form_id:f.id||"unnamed",page_path:location.pathname});},true);
})();