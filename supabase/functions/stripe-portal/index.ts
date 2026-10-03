import { createClient } from "npm:@supabase/supabase-js@2";

const cors = {
  "Access-Control-Allow-Origin": "https://ahorraencasaya.es",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Content-Type": "application/json"
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: cors });
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ error: "Method not allowed" }, 405);

  try {
    const authHeader = req.headers.get("Authorization");
    if (!authHeader?.startsWith("Bearer ")) return json({ error: "Authentication required" }, 401);

    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_ANON_KEY")!,
      { global: { headers: { Authorization: authHeader } } }
    );
    const { data: { user }, error: userError } = await supabase.auth.getUser();
    if (userError || !user) return json({ error: "Invalid session" }, 401);

    const admin = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
    );
    const { data: subscription } = await admin
      .from("subscriptions")
      .select("provider_customer_id,status")
      .eq("user_id", user.id)
      .eq("provider", "stripe")
      .maybeSingle();

    if (!subscription?.provider_customer_id) {
      return json({ error: "No Stripe customer is associated with this account." }, 404);
    }

    const stripeSecret = Deno.env.get("STRIPE_SECRET_KEY");
    if (!stripeSecret) return json({ error: "Stripe is not configured yet" }, 503);

    const params = new URLSearchParams({
      customer: subscription.provider_customer_id,
      return_url: "https://ahorraencasaya.es/cuenta/"
    });
    const response = await fetch("https://api.stripe.com/v1/billing_portal/sessions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${stripeSecret}`,
        "Content-Type": "application/x-www-form-urlencoded"
      },
      body: params
    });
    const portal = await response.json();
    if (!response.ok) {
      console.error("Stripe Portal error", portal);
      return json({ error: "Stripe could not create the customer portal." }, 502);
    }

    return json({ url: portal.url });
  } catch (error) {
    console.error(error);
    return json({ error: "Unexpected portal error." }, 500);
  }
});
