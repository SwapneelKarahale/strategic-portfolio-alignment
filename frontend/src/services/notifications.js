import api, { unwrap } from "./api";

export function listNotifications(params) {
  return unwrap(api.get("/notifications", { params }));
}

export function markNotificationRead(id) {
  return unwrap(api.patch(`/notifications/${id}/read`));
}
