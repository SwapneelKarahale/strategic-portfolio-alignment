import api from "./api";

export function listAuditLogs(params) {
  return api.get("/audit-logs", { params }).then((res) => res.data);
}
