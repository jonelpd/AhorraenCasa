(() => {
  const dataUrl = new URL("../data/amazon-products-live.json", document.currentScript?.src || location.href);
  const money = (p) => p ? new Intl.NumberFormat("es-ES",{style:"currency",currency:p.currency||"EUR"}).format(p.amount) : "Consultar en Amazon";
  async function run(){
    const res = await fetch(dataUrl);
    if(!res.ok) throw new Error("Amazon data unavailable");
    const data = await res.json();
    document.querySelectorAll("[data-amazon-key]").forEach(el => {
      const key=el.dataset.amazonKey;
      const p=(data.products||{})[key];
      if(!p) return;
      const price=el.querySelector(".amazon-price");
      const link=el.querySelector("a");
      if(price) price.textContent=p.price ? money(p.price) : "Consultar en Amazon";
      if(link && p.url) link.href=p.url;
      if(p.title) el.setAttribute("aria-label",p.title);
    });
    document.querySelectorAll("[data-amazon-updated]").forEach(el=>{
      if(data.updatedAt){
        const d=new Date(data.updatedAt);
        el.textContent="Precio y disponibilidad consultados en Amazon el "+d.toLocaleString("es-ES",{dateStyle:"short",timeStyle:"short"})+".";
      }
    });
  }
  run().catch(()=>{});
})();