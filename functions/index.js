const { onCall, HttpsError } = require("firebase-functions/v2/https");
const { defineSecret } = require("firebase-functions/params");
const admin = require("firebase-admin");
admin.initializeApp();

const slackWebhookUrl = defineSecret("SLACK_OPERATION_HIRED_WEBHOOK_URL");

exports.subscribeEmail = onCall(
  { secrets: [slackWebhookUrl] },
  async (request) => {
    const { email, source, website } = request.data;

    // Honeypot — bots fill hidden fields, humans don't
    if (website) {
      return { status: "subscribed" };
    }

    // Validate email
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
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

    // Send Slack notification to #intent-notifier
    try {
      const webhookUrl = slackWebhookUrl.value();
      if (webhookUrl) {
        await fetch(webhookUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            text: `New email signup: *${email.toLowerCase()}* (from ${source} form)`,
          }),
        });
      }
    } catch (slackErr) {
      console.error("Slack notification failed:", slackErr);
    }

    return { status: "subscribed" };
  }
);
