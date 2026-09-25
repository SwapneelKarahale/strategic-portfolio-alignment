import api from "./api";

export function listDemands(params) {
  return api.get("/demands", { params }).then((res) => res.data);
}

export function getDemand(id) {
  return api.get(`/demands/${id}`).then((res) => res.data.data);
}

export function createDemand(payload) {
  return api.post("/demands", payload).then((res) => res.data.data);
}

export function updateDemand(id, payload) {
  return api.patch(`/demands/${id}`, payload).then((res) => res.data.data);
}

export function reviewDemand(id, action, comments) {
  return api.post(`/demands/${id}/review`, { action, comments }).then((res) => res.data.data);
}

export function convertDemand(id) {
  return api.post(`/demands/${id}/convert`).then((res) => res.data.data);
}
