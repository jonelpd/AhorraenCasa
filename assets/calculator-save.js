(function(){
  function esc(v){return String(v??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]))}
  function money(v){return Number(v||0).toLocaleString("es-ES",{style:"currency",currency:"EUR"})}
  async function saveResult(options){
    const button=options.button;
    if(!button)return;
    button.disabled=true;
    const original=button.textContent;
    try{
      const c=await AhorraAuth.getClient();
      const session=await AhorraAuth.getSession();
      if(!session){
        const next=location.href;
        location.href="../cuenta/login.html?next="+encodeURIComponent(next);
        return;
      }
      const monthlyCost=Number(options.monthlyCost||0);
      const annualCost=Number(options.annualCost||0);
      const monthlySaving=Number(options.monthlySaving||0);
      const annualSaving=Number(options.annualSaving||0);
      const payload={
        user_id:session.user.id,
        calculator_key:String(options.calculatorKey||"general"),
        calculator_name:String(options.calculatorName||"Calculadora"),
        month:new Date().toISOString().slice(0,7)+"-01",
        monthly_cost:Math.max(0,monthlyCost),
        annual_cost:Math.max(0,annualCost),
        monthly_saving:Math.max(0,monthlySaving),
        annual_saving:Math.max(0,annualSaving),
        details:options.details||{}
      };
      const {error}=await c.from("calculator_results").insert(payload);
      if(error)throw error;
      button.textContent="✓ Guardado en Mi ahorro";
      button.classList.add("saved");
      if(options.message){
        const el=document.querySelector(options.message);
        if(el)el.textContent="Resultado guardado en tu cuenta.";
      }
      setTimeout(()=>{button.textContent=original;button.disabled=false},2800);
    }catch(e){
      button.disabled=false;
      button.textContent=original;
      const message=e?.message||"No se pudo guardar el resultado.";
      const el=document.querySelector(options.message);
      if(el)el.textContent=message;
      else alert(message);
    }
  }
  window.AhorraCalculator={saveResult,money,esc};
})();