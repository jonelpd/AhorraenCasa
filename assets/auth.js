(function(){
  const CDN="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2";
  let clientPromise=null;
  function getClient(){
    if(clientPromise) return clientPromise;
    clientPromise=new Promise((resolve,reject)=>{
      if(!window.AHORRA_SUPABASE_URL || !window.AHORRA_SUPABASE_KEY){
        reject(new Error("Supabase no está configurado todavía."));
        return;
      }
      const start=()=>{
        if(!window.supabase){reject(new Error("No se pudo cargar Supabase."));return;}
        resolve(window.supabase.createClient(window.AHORRA_SUPABASE_URL,window.AHORRA_SUPABASE_KEY));
      };
      if(window.supabase) start();
      else {const s=document.createElement("script");s.src=CDN;s.onload=start;s.onerror=()=>reject(new Error("No se pudo cargar Supabase."));document.head.appendChild(s);}
    });
    return clientPromise;
  }
  async function getSession(){const c=await getClient();return (await c.auth.getSession()).data.session;}
  async function requireSession(redirect){
    try{const s=await getSession();if(!s){location.href=redirect||"cuenta/login.html";return null;}return s;}
    catch(e){showError(e);return null;}
  }
  async function getProfile(session){
    const c=await getClient();
    const r=await c.from("profiles").select("id,full_name,role").eq("id",session.user.id).maybeSingle();
    if(r.error) throw r.error;
    return r.data;
  }
  function showError(e){
    document.querySelectorAll("[data-auth-error]").forEach(el=>{el.hidden=false;el.textContent=e?.message||"No se pudo completar la operación."});
  }
  window.AhorraAuth={getClient,getSession,requireSession,getProfile,showError};
})();