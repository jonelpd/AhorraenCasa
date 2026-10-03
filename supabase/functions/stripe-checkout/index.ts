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

function stripeForm(data: Record<string, string>) {
  return new URLSearchParams(data);
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

    const body = await req.json();
    const plan = body?.plan === "annual" ? "annual" : body?.plan === "monthly" ? "monthly" : null;
    if (!plan) return json({ error: "Invalid plan" }, 400);

    const priceId = plan === "annual"
      ? Deno.env.get("STRIPE_ANNUAL_PRICE_ID")
      : Deno.env.get("STRIPE_MONTHLY_PRICE_ID");
    if (!priceId) return json({ error: "Stripe price is not configured yet" }, 503);

    const stripeSecret = Deno.env.get("STRIPE_SECRET_KEY");
    if (!stripeSecret) return json({ error: "Stripe is not configured yet" }, 503);

    const admin = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
    );
    const { data: existing } = await admin
      .from("subscriptions")
      .select("provider_customer_id,status")
      .eq("user_id", user.id)
      .eq("provider", "stripe")
      .maybeSingle();

    if (existing?.status === "active" || existing?.status === "trialing") {
      return json({ error: "An active Premium subscription already exists." }, 409);
    }

    const params: Record<string, string> = {
      mode: "subscription",
      "line_items[0][price]": priceId,
      "line_items[0][quantity]": "1",
      success_url: "https://ahorraencasaya.es/premium/planes.html?checkout=success",
      cancel_url: "https://ahorraencasaya.es/premium/planes.html?checkout=cancel",
      client_reference_id: user.id,
      "metadata[user_id]": user.id,
      "metadata[plan]": plan,
      "subscription_data[metadata][user_id]": user.id,
      "subscription_data[metadata][plan]": plan,
      "subscription_data[metadata][site]": "ahorraencasaya.es",
      customer_email: user.email ?? ""
    };

    if (existing?.provider_customer_id) params.customer = existing.provider_customer_id;

    const response = await fetch("https://api.stripe.com/v1/checkout/sessions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${stripeSecret}`,
        "Content-Type": "application/x-www-form-urlencoded"
      },
      body: stripeForm(params)
    });

    const session = await response.json();
    if (!response.ok) {
      console.error("Stripe Checkout error", session);
      return json({ error: "Stripe could not create the checkout session." }, 502);
    }

    return json({ url: session.url });
  } catch (error) {
    console.error(error);
    return json({ error: "Unexpected checkout error." }, 500);
  }
});
