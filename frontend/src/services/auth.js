import api, { unwrap } from "./api";

export function login(email, password) {
  return unwrap(api.post("/auth/login", { email, password }));
}

export function fetchCurrentUser() {
  return unwrap(api.get("/auth/me"));
}
