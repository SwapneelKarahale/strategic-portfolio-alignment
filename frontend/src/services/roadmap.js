import api, { unwrap } from "./api";

export function getRoadmap(params) {
  return unwrap(api.get("/roadmap", { params }));
}

export function scheduleProject(payload) {
  return unwrap(api.post("/roadmap", payload));
}
