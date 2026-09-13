import assert from "node:assert/strict";
import test from "node:test";
import { isConfigured, isOneMinuteBefore, parseWib, salesCloseAt } from "./index.js";

test("reads JKT48 General close time as WIB", () => {
  assert.equal(
    salesCloseAt({ sales_period: [{ label: "General", end_date: "2026-09-13T10:00:00" }] }),
    Date.parse("2026-09-13T10:00:00+07:00"),
  );
  assert.equal(parseWib("invalid"), null);
});

test("only runs during the minute before close", () => {
  const close = Date.parse("2026-09-13T10:00:00+07:00");
  assert.equal(isOneMinuteBefore(close, Date.parse("2026-09-13T09:59:40+07:00")), true);
  assert.equal(isOneMinuteBefore(close, Date.parse("2026-09-13T09:58:59+07:00")), false);
  assert.equal(isOneMinuteBefore(close, close), false);
});

test("does not contact upstream until Telegram is configured", () => {
  assert.equal(isConfigured({}), false);
  assert.equal(isConfigured({ TELEGRAM_BOT_TOKEN: "token", TELEGRAM_CHAT_ID: "123" }), true);
});
