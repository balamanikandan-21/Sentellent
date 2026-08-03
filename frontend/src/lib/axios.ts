import axios from "axios"

export const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
})

let isRefreshing = false
let failedQueue: Array<{
  resolve: (v: unknown) => void
  reject: (e: unknown) => void
}> = []

function processQueue(error: unknown) {
  failedQueue.forEach((p) => {
    if (error) p.reject(error)
    else p.resolve(undefined)
  })
  failedQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config

    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error)
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject })
      }).then(() => api(original))
    }

    original._retry = true
    isRefreshing = true

    try {
      await api.post("/auth/refresh")
      processQueue(null)
      return api(original)
    } catch (refreshError) {
      processQueue(refreshError)
      if (typeof window !== "undefined") {
        window.location.href = "/login"
      }
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  },
)
