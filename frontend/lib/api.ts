import axios from "axios";

const API_BASE = "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE,
});

// Attach token to every request
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const res = await axios.post(`${API_BASE}/auth/refresh`, {
            refresh_token: refresh,
          });
          localStorage.setItem("access_token", res.data.access_token);
          localStorage.setItem("refresh_token", res.data.refresh_token);
          error.config.headers.Authorization = `Bearer ${res.data.access_token}`;
          return axios(error.config);
        } catch {
          localStorage.clear();
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

// Auth
export const authAPI = {
  register: (data: { email: string; password: string; role: string }) =>
    api.post("/auth/register", data),
  login: (data: { email: string; password: string }) =>
    api.post("/auth/login", data),
  me: () => api.get("/auth/me"),
};

// Worker
export const workerAPI = {
  getProfile: () => api.get("/worker/profile"),
  updateProfile: (data: object) => api.patch("/worker/profile", data),
  getSkills: () => api.get("/worker/skills"),
  addSkill: (data: { skill_name: string; skill_category?: string }) =>
    api.post("/worker/skills", data),
  deleteSkill: (id: string) => api.delete(`/worker/skills/${id}`),
  getVideos: () => api.get("/worker/videos"),
  uploadVideo: (file: File, onProgress?: (p: number) => void) => {
    const form = new FormData();
    form.append("file", file);
    return api.post("/worker/videos/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (e) => {
        if (onProgress && e.total) {
          onProgress(Math.round((e.loaded * 100) / e.total));
        }
      },
    });
  },
  getMatches: () => api.get("/worker/matches"),
};

// Employer
export const employerAPI = {
  getProfile: () => api.get("/employer/profile"),
  updateProfile: (data: object) => api.patch("/employer/profile", data),
  getJobs: () => api.get("/employer/jobs"),
  createJob: (data: object) => api.post("/employer/jobs", data),
  deleteJob: (id: string) => api.delete(`/employer/jobs/${id}`),
  getPublicJobs: () => api.get("/employer/public/jobs"),
  getJobCandidates: (jobId: string) => api.get(`/employer/jobs/${jobId}/candidates`),
};