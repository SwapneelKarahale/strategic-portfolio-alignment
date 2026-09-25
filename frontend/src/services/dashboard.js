import api, { unwrap } from "./api";

export function getSummary(params) {
  return unwrap(api.get("/dashboard/summary", { params }));
}

export function getAnalytics(params) {
  return unwrap(api.get("/dashboard/analytics", { params }));
}
