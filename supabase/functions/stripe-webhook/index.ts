import { createClient } from "npm:@supabase/supabase-js@2";

const encoder = new TextEncoder();

function timingSafeEqual(a: Uint8Array, b: Uint8Array) {
  if (a.length !== b.length) return false;
  let result = 0;
  for (let i = 0; i < a.length; i++) result |= a[i] ^ b[i];
  return result === 0;
}

function hexToBytes(hex: string) {
  const out = new Uint8Array(hex.length / 2);
  for (let i = 0; i < out.length; i++) out[i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
  return out;
}

async function verifyStripeSignature(payload: string, header: string, secret: string) {
  const parts = Object.fromEntries(header.split(",").map(part => {
    const [key, value] = part.split("=");
    return [key, value];
  }));
  const timestamp = parts.t;
  const signature = parts.v1;
  if (!timestamp || !signature) return false;

  const age = Math.abs(Date.now() / 1000 - Number(timestamp));
  if (!Number.isFinite(age) || age > 300) return false;

  const key = await crypto.subtle.importKey(
    "raw", encoder.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  const signed = `${timestamp}.${payload}`;
  const digest = new Uint8Array(await crypto.subtle.sign("HMAC", key, encoder.encode(signed)));
  return timingSafeEqual(digest, hexToBytes(signature));
}

function iso(unix?: number | null) {
  return unix ? new Date(unix * 1000).toISOString() : null;
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return new Response("Method not allowed", { status: 405 });

  const signature = req.headers.get("Stripe-Signature");
  const secret = Deno.env.get("STRIPE_WEBHOOK_SECRET");
  if (!signature || !secret) return new Response("Webhook not configured", { status: 503 });

  const payload = await req.text();
  if (!(await verifyStripeSignature(payload, signature, secret))) {
    return new Response("Invalid signature", { status: 400 });
  }

  try {
    const event = JSON.parse(payload);
    const admin = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
    );

    const { error: eventInsertError } = await admin
      .from("stripe_events")
      .insert({ event_id: event.id, event_type: event.type });
    if (eventInsertError) {
      if (eventInsertError.code === "23505") return new Response(JSON.stringify({ received: true, duplicate: true }), { status: 200, headers: { "Content-Type": "application/json" } });
      throw eventInsertError;
    }

    if (event.type === "checkout.session.completed") {
      const session = event.data.object;
      if (session.mode === "subscription" && session.subscription && session.customer) {
        const userId = session.metadata?.user_id || session.client_reference_id;
        if (userId) {
          await admin.from("subscriptions").upsert({
            user_id: userId,
            provider: "stripe",
            provider_customer_id: session.customer,
            provider_subscription_id: session.subscription,
            provider_price_id: null,
            status: "active",
            updated_at: new Date().toISOString()
          }, { onConflict: "user_id,provider" });
        }
      }
    }

    if (event.type === "customer.subscription.created" ||
        event.type === "customer.subscription.updated" ||
        event.type === "customer.subscription.deleted") {
      const subscription = event.data.object;
      const userId = subscription.metadata?.user_id;
      let query = admin.from("subscriptions").select("user_id").eq("provider","stripe").eq("provider_subscription_id",subscription.id).maybeSingle();
      const { data: existing } = await query;
      const resolvedUserId = userId || existing?.user_id;

      if (resolvedUserId) {
        await admin.from("subscriptions").upsert({
          user_id: resolvedUserId,
          provider: "stripe",
          provider_customer_id: subscription.customer,
          provider_subscription_id: subscription.id,
          provider_price_id: subscription.items?.data?.[0]?.price?.id || null,
          status: subscription.status,
          current_period_start: iso(subscription.current_period_start),
          current_period_end: iso(subscription.current_period_end),
          cancel_at_period_end: Boolean(subscription.cancel_at_period_end),
          trial_end: iso(subscription.trial_end),
          updated_at: new Date().toISOString()
        }, { onConflict: "user_id,provider" });
      }
    }

    return new Response(JSON.stringify({ received: true }), {
      status: 200,
      headers: { "Content-Type": "application/json" }
    });
  } catch (error) {
    console.error(error);
    return new Response("Webhook processing failed", { status: 500 });
  }
});
