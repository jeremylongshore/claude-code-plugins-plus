const { onCall, HttpsError } = require("firebase-functions/v2/https");
const { defineSecret } = require("firebase-functions/params");
const admin = require("firebase-admin");
admin.initializeApp();

const slackWebhookUrl = defineSecret("SLACK_OPERATION_HIRED_WEBHOOK_URL");

// Simple in-memory rate limiter (resets on cold start, ~5 min window)
const rateLimitMap = new Map();
const RATE_LIMIT_WINDOW_MS = 60_000; // 1 minute
const RATE_LIMIT_MAX = 5; // max requests per IP per window

function checkRateLimit(request) {
  const ip =
    request.rawRequest?.headers?.["x-forwarded-for"]?.split(",")[0]?.trim() ||
    request.rawRequest?.ip ||
    "unknown";
  const now = Date.now();
  const entry = rateLimitMap.get(ip);

  if (entry && now - entry.windowStart < RATE_LIMIT_WINDOW_MS) {
    entry.count++;
    if (entry.count > RATE_LIMIT_MAX) {
      throw new HttpsError("resource-exhausted", "Too many requests. Try again later.");
    }
  } else {
    rateLimitMap.set(ip, { windowStart: now, count: 1 });
  }

  // Prune stale entries every 100 calls to prevent memory leak
  if (rateLimitMap.size > 1000) {
    for (const [key, val] of rateLimitMap) {
      if (now - val.windowStart > RATE_LIMIT_WINDOW_MS * 5) {
        rateLimitMap.delete(key);
      }
    }
  }
}

exports.subscribeEmail = onCall(
  { secrets: [slackWebhookUrl] },
  async (request) => {
    checkRateLimit(request);

    const { email, source, website } = request.data;

    // Honeypot — bots fill hidden fields, humans don't
    if (website) {
      return { status: "subscribed" };
    }

    // Validate email
    if (!email || typeof email !== "string" || email.length > 254 ||
        !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      throw new HttpsError("invalid-argument", "Valid email required");
    }

    // Validate source
    const allowedSources = ["footer", "homepage", "killer-skills"];
    if (!source || !allowedSources.includes(source)) {
      throw new HttpsError("invalid-argument", "Invalid source provided");
    }

    const db = admin.firestore();

    // Check for duplicate
    const existing = await db
      .collection("email-signups")
      .where("email", "==", email.toLowerCase())
      .limit(1)
      .get();
    if (!existing.empty) {
      return { status: "already_subscribed" };
    }

    // Save to Firestore
    await db.collection("email-signups").add({
      email: email.toLowerCase(),
      source,
      subscribedAt: admin.firestore.FieldValue.serverTimestamp(),
    });

    // Send Slack notification
    try {
      const webhookUrl = slackWebhookUrl.value();
      if (!webhookUrl) {
        console.error("Slack webhook URL not configured");
      } else {
        const resp = await fetch(webhookUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            text: `New email signup: *${email.toLowerCase()}* (from ${source} form)`,
          }),
        });
        if (!resp.ok) {
          const body = await resp.text();
          console.error(`Slack webhook returned ${resp.status}: ${body}`);
        } else {
          console.log(`Slack notification sent for ${email.toLowerCase()}`);
        }
      }
    } catch (slackErr) {
      console.error("Slack notification failed:", slackErr);
    }

    return { status: "subscribed" };
  }
);

exports.submitNomination = onCall(
  { secrets: [slackWebhookUrl] },
  async (request) => {
    checkRateLimit(request);

    const { repoUrl, source, website } = request.data;

    // Honeypot
    if (website) return { status: "submitted" };

    // Validate GitHub URL (strict: must be github.com, max length, no query params)
    if (!repoUrl || typeof repoUrl !== "string" || repoUrl.length > 200 ||
        !/^https:\/\/github\.com\/[a-zA-Z0-9._-]+\/[a-zA-Z0-9._-]+\/?$/.test(repoUrl)) {
      throw new HttpsError("invalid-argument", "Valid GitHub repo URL required");
    }

    // Validate source
    const allowedSources = ["killer-skills"];
    if (!source || !allowedSources.includes(source)) {
      throw new HttpsError("invalid-argument", "Invalid source provided");
    }

    const cleanUrl = repoUrl.replace(/\/+$/, "").toLowerCase();
    const db = admin.firestore();

    // Dedupe
    const existing = await db
      .collection("nominations")
      .where("repoUrl", "==", cleanUrl)
      .limit(1)
      .get();
    if (!existing.empty) return { status: "already_nominated" };

    // Save to Firestore
    await db.collection("nominations").add({
      repoUrl: cleanUrl,
      source,
      submittedAt: admin.firestore.FieldValue.serverTimestamp(),
      status: "pending",
    });

    // Slack notification
    try {
      const webhookUrl = slackWebhookUrl.value();
      if (!webhookUrl) {
        console.error("Slack webhook URL not configured");
      } else {
        const resp = await fetch(webhookUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            text: `New Killer Skill nomination: *<${cleanUrl}|${cleanUrl.replace("https://github.com/", "")}>* (from ${source} form)`,
          }),
        });
        if (!resp.ok) {
          const body = await resp.text();
          console.error(`Slack webhook returned ${resp.status}: ${body}`);
        } else {
          console.log(`Slack notification sent for nomination ${cleanUrl}`);
        }
      }
    } catch (slackErr) {
      console.error("Slack notification failed:", slackErr);
    }

    return { status: "submitted" };
  }
);
