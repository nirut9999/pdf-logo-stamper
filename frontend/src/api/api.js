import axios from 'axios'

// axios instance กลาง — ทุก API call ผ่านไฟล์นี้เท่านั้น (ตาม convention workspace)
// baseURL ว่าง = ใช้ relative '/api/...' (vite proxy ตอน dev, nginx proxy ตอน prod)
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '',
  timeout: 120000,
})

export default api
