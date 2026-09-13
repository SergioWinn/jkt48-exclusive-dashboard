const API = "https://jkt48.com/api/v1/exclusives";
const WATCHLIST_KEY = "watchlist";
const WATCHLIST_MAX_AGE_MS = 6 * 60 * 60 * 1000;

export function parseWib(value) {
  if (!value || typeof value !== "string") return null;
  const normalized = value.endsWith("Z") ? value : `${value.replace(/\.\d+$/, "")}+07:00`;
  const timestamp = Date.parse(normalized);
  return Number.isNaN(timestamp) ? null : timestamp;
}

export function salesCloseAt(event) {
  const general = event?.sales_period?.find(
    (period) => period?.label?.toLowerCase() === "general",
  );
  return parseWib(general?.end_date ?? event?.valid_date_to);
}

export function isOneMinuteBefore(closeAt, now) {
  return Math.floor(closeAt / 60_000) - Math.floor(now / 60_000) === 1;
}

export function isConfigured(env) {
  return Boolean(env.TELEGRAM_BOT_TOKEN && env.TELEGRAM_CHAT_ID);
}

async function getJson(url, env) {
  const response = await fetch(url, {
    headers: {
      Accept: "application/json",
      Referer: "https://jkt48.com/",
      ...(env.JKT48_COOKIE ? { Cookie: env.JKT48_COOKIE } : {}),
    },
  });
  if (!response.ok || !response.headers.get("content-type")?.includes("json")) {
    throw new Error(`JKT48 API HTTP ${response.status}`);
  }
  const payload = await response.json();
  if (payload?.status !== true) throw new Error(payload?.message || "Invalid JKT48 API response");
  return payload.data;
}

function eventList(data) {
  return Array.isArray(data) ? data : data?.data ?? [];
}

async function refreshWatchlist(env, now) {
  const events = eventList(await getJson(`${API}?lang=id`, env));
  // The list API commonly omits sales_period, so its detail is the only reliable close time.
  const details = await Promise.all(
    events.filter((event) => event.code).map(
      (event) => getJson(`${API}/${encodeURIComponent(event.code)}?lang=id`, env),
    ),
  );
  const watchlist = details
    .map((event) => ({
      code: event.code,
      title: event.title || event.code,
      closeAt: salesCloseAt(event),
    }))
    .filter((event) => event.code && event.closeAt && event.closeAt > now);

  await env.SNAPSHOTS.put(WATCHLIST_KEY, JSON.stringify({ refreshedAt: now, events: watchlist }));
  return watchlist;
}

async function getWatchlist(env, now) {
  const cached = await env.SNAPSHOTS.get(WATCHLIST_KEY, "json");
  if (cached?.refreshedAt && now - cached.refreshedAt < WATCHLIST_MAX_AGE_MS) return cached.events || [];
  return refreshWatchlist(env, now);
}

function closeLabel(timestamp) {
  return new Intl.DateTimeFormat("id-ID", {
    timeZone: "Asia/Jakarta",
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(timestamp));
}

function snapshotSummary(event, bonus, closeAt) {
  const sessions = Array.isArray(bonus) ? bonus : [];
  const lines = sessions.map((session) => {
    const available = (session.session_members || []).reduce(
      (sum, member) => sum + Math.max(0, Number(member.available_quota) || 0),
      0,
    );
    return `${session.date || "-"} ${session.label || "Sesi"}: ${available} slot tersisa`;
  });
  return [
    `Snapshot H-1 menit · ${event.title || event.code}`,
    `Penjualan tutup: ${closeLabel(closeAt)} WIB`,
    `Bonus API: ${sessions.length} sesi`,
    ...lines.slice(0, 20),
    lines.length > 20 ? `+ ${lines.length - 20} sesi lain di file JSON.` : "",
  ].filter(Boolean).join("\n");
}

async function sendTelegramSnapshot(env, event, bonus, closeAt, capturedAt) {
  const snapshot = {
    captured_at: new Date(capturedAt).toISOString(),
    close_at: new Date(closeAt).toISOString(),
    event,
    bonus,
  };
  const filename = `${event.code}-${new Date(closeAt).toISOString().replace(/[:.]/g, "-")}.json`;
  const form = new FormData();
  form.set("chat_id", env.TELEGRAM_CHAT_ID);
  form.set("caption", snapshotSummary(event, bonus, closeAt));
  form.set("document", new Blob([JSON.stringify(snapshot, null, 2)], { type: "application/json" }), filename);
  const response = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendDocument`, {
    method: "POST",
    body: form,
  });
  if (!response.ok || !(await response.json()).ok) throw new Error("Telegram delivery failed");
  return snapshot;
}

async function processClose(env, event, now) {
  const sentKey = `sent/${event.code}/${event.closeAt}`;
  if (await env.SNAPSHOTS.get(sentKey)) return;

  const [primary, bonus] = await Promise.all([
    getJson(`${API}/${encodeURIComponent(event.code)}?lang=id`, env),
    getJson(`${API}/${encodeURIComponent(event.code)}/bonus?lang=id`, env),
  ]);
  if (!Array.isArray(bonus) || !bonus.length) throw new Error("Bonus API has no snapshot data");
  const snapshot = await sendTelegramSnapshot(env, primary, bonus, event.closeAt, now);
  await Promise.all([
    env.SNAPSHOTS.put(`snapshot/${event.code}/${event.closeAt}.json`, JSON.stringify(snapshot)),
    env.SNAPSHOTS.put(sentKey, new Date(now).toISOString()),
  ]);
}

export default {
  async scheduled(controller, env, ctx) {
    if (!isConfigured(env)) return;
    const now = controller.scheduledTime || Date.now();
    ctx.waitUntil((async () => {
      const events = await getWatchlist(env, now);
      await Promise.all(events.filter((event) => isOneMinuteBefore(event.closeAt, now)).map(
        (event) => processClose(env, event, now),
      ));
    })());
  },
};
