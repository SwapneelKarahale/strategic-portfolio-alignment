import api, { unwrap } from "./api";

export function listBusinessFunctions() {
  return unwrap(api.get("/business-functions"));
}

export function listCapabilities() {
  return unwrap(api.get("/capabilities"));
}

export function listUsers(role) {
  return unwrap(api.get("/users", { params: role ? { role } : {} }));
}
