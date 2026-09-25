import api from "./api";

export function listProjects(params) {
  return api.get("/projects", { params }).then((res) => res.data);
}

export function getProject(id) {
  return api.get(`/projects/${id}`).then((res) => res.data.data);
}

export function updateProject(id, payload) {
  return api.patch(`/projects/${id}`, payload).then((res) => res.data.data);
}

export function addRequirement(id, payload) {
  return api.post(`/projects/${id}/requirements`, payload).then((res) => res.data.data);
}

export function addCapability(id, payload) {
  return api.post(`/projects/${id}/capabilities`, payload).then((res) => res.data.data);
}

export function addMilestone(id, payload) {
  return api.post(`/projects/${id}/milestones`, payload).then((res) => res.data.data);
}

export function updateMilestone(projectId, milestoneId, payload) {
  return api.patch(`/projects/${projectId}/milestones/${milestoneId}`, payload).then((res) => res.data.data);
}

export function updateProjectStatus(id, payload) {
  return api.patch(`/projects/${id}/status`, payload).then((res) => res.data.data);
}
