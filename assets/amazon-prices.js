(() => {
  const dataUrl = new URL("../data/amazon-products-live.json", document.currentScript?.src || location.href);
  const money = (p) => p
    ? new Intl.NumberFormat("es-ES", {style:"currency", currency:p.currency || "EUR"}).format(p.amount)
    : "Consultar en Amazon";
  const partnerTag = "jonelpd-21";

  const affiliate = (raw) => {
    try {
      const u = new URL(raw, location.href);
      if (!u.hostname.endsWith("amazon.es")) return raw;

      if (u.pathname === "/" || u.pathname === "") {
        u.pathname = "/s";
        u.searchParams.set("k", "productos ahorro energia");
      }

      // Para búsquedas de Amazon, priorizar el orden de menor a mayor precio.
      // No almacenamos historial ni mostramos alertas de cambios de precio.
      if (u.pathname === "/s" && !u.searchParams.has("s")) {
        u.searchParams.set("s", "price-asc-rank");
      }

      u.searchParams.set("tag", partnerTag);
      return u.toString();
    } catch(e) {
      return raw;
    }
  };

  async function run() {
    const res = await fetch(dataUrl);
    if (!res.ok) throw new Error("Amazon data unavailable");
    const data = await res.json();

    document.querySelectorAll("[data-amazon-key]").forEach(el => {
      const key = el.dataset.amazonKey;
      const p = (data.products || {})[key];
      if (!p) return;

      const price = el.querySelector(".amazon-price");
      const link = el.querySelector("a");

      if (price) price.textContent = p.price
        ? money(p.price)
        : "Consultar en Amazon";

      if (link) link.href = affiliate(p.url || link.href);

      if (p.title) el.setAttribute("aria-label", p.title);
    });

    document.querySelectorAll("[data-amazon-updated]").forEach(el => {
      if (data.updatedAt) {
        const d = new Date(data.updatedAt);
        el.textContent =
          "Información de Amazon consultada el " +
          d.toLocaleString("es-ES", {dateStyle:"short", timeStyle:"short"}) +
          ". El precio aplicable es el que muestre Amazon al comprar.";
      }
    });
  }

  document.querySelectorAll('a[href*="amazon.es"]').forEach(a => {
    a.href = affiliate(a.href);
  });

  run().catch(() => {});
})();
