import { defineStore } from 'pinia'
import { ref, reactive, computed, watch } from 'vue'
import api from '../api/api'

// Store เดียวที่เป็น source of truth — component ห้ามเรียก axios ตรงๆ
export const useStamper = defineStore('stamper', () => {
  const logos = ref([])
  const pdfs = ref([])
  const fonts = ref(['Helvetica-Bold'])
  const presets = ref([])
  const editingPresetId = ref(null)   // preset ที่เปิดอยู่ (บันทึก = เขียนทับ)
  const selectedLogoId = ref(null)
  const selectedPdfIds = ref([])   // ที่จะ stamp (ค่า default = ทุกไฟล์ที่อัปโหลด)
  const previewPdfId = ref(null)
  const previewPage = ref(1)
  const previewUrl = ref(null)

  const status = reactive({ previewLoading: false, stamping: false, error: null, notice: null })

  const options = reactive({
    logo_width_mm: 30,
    logo_height_mm: null,   // null = คงสัดส่วน
    margin_top_mm: 8,
    margin_right_mm: 8,
    opacity: 0.6,           // watermark default — มองทะลุ
    page_scope: 'all',      // 'all' | 'first' | 'custom'
    custom_pages: '',       // เช่น '1-3,5' เมื่อ page_scope='custom'
    rotation_degrees: 0,    // เอียง (บวก = ตามเข็ม)
    include_text: true,     // ข้อความข้างโลโก้ (ขวา)
    text_template: 'COPY No.{n}',
    text_color: '#CC0000',
    text_size_mm: 5,        // ขนาดข้อความอิสระจากโลโก้ (NULL = backend auto)
    text_font: 'Helvetica-Bold',
    copies: 1,              // จำนวนสำเนา 1..200
  })
  const previewCopy = ref(1)  // เลขสำเนาที่แสดงใน preview

  const selectedLogo = computed(() => logos.value.find((l) => l.id === selectedLogoId.value) || null)
  const previewPdf = computed(() => pdfs.value.find((p) => p.id === previewPdfId.value) || null)
  const canPreview = computed(() => !!selectedLogoId.value && !!previewPdfId.value)
  const targetsToStamp = computed(() =>
    selectedPdfIds.value.length ? selectedPdfIds.value : pdfs.value.map((p) => p.id)
  )
  const totalOutputs = computed(() => targetsToStamp.value.length * Math.max(1, Number(options.copies) || 1))

  function _payload() {
    return {
      logo_width_mm: Number(options.logo_width_mm),
      logo_height_mm: options.logo_height_mm ? Number(options.logo_height_mm) : null,
      margin_top_mm: Number(options.margin_top_mm),
      margin_right_mm: Number(options.margin_right_mm),
      opacity: Number(options.opacity),
      page_scope: options.page_scope === 'custom' ? (options.custom_pages.trim() || 'all') : options.page_scope,
      rotation_degrees: Number(options.rotation_degrees) || 0,
      include_text: !!options.include_text,
      text_template: options.text_template || 'COPY No.{n}',
      text_color: options.text_color || '#CC0000',
      text_size_mm: options.text_size_mm ? Number(options.text_size_mm) : null,
      text_font: options.text_font || 'Helvetica-Bold',
      copies: Math.min(200, Math.max(1, Number(options.copies) || 1)),
    }
  }

  // ---------- logos ----------
  async function loadLogos() {
    const { data } = await api.get('/api/logos')
    logos.value = data
    if (!selectedLogoId.value && data.length) selectedLogoId.value = data[0].id
  }
  async function uploadLogo(file) {
    const fd = new FormData()
    fd.append('file', file)
    const { data } = await api.post('/api/logos', fd)
    logos.value.push(data)
    selectedLogoId.value = data.id
    status.notice = `เพิ่มโลโก้ "${data.filename}" แล้ว`
    schedulePreview()
  }
  async function deleteLogo(id) {
    await api.delete(`/api/logos/${id}`)
    logos.value = logos.value.filter((l) => l.id !== id)
    if (selectedLogoId.value === id) selectedLogoId.value = logos.value[0]?.id ?? null
  }

  // ---------- pdfs ----------
  async function loadPdfs() {
    const { data } = await api.get('/api/pdfs')
    pdfs.value = data
    selectedPdfIds.value = data.map((p) => p.id)
    if (!previewPdfId.value && data.length) previewPdfId.value = data[0].id
  }
  async function uploadPdfs(fileList) {
    const fd = new FormData()
    for (const f of fileList) fd.append('files', f)
    const { data } = await api.post('/api/pdfs', fd)
    pdfs.value.push(...data)
    selectedPdfIds.value = pdfs.value.map((p) => p.id)
    if (!previewPdfId.value && data.length) { previewPdfId.value = data[0].id; previewPage.value = 1 }
    status.notice = `เพิ่ม PDF ${data.length} ไฟล์`
    schedulePreview()
  }
  async function removePdf(id) {
    await api.delete(`/api/pdfs/${id}`)
    pdfs.value = pdfs.value.filter((p) => p.id !== id)
    selectedPdfIds.value = selectedPdfIds.value.filter((x) => x !== id)
    if (previewPdfId.value === id) { previewPdfId.value = pdfs.value[0]?.id ?? null; previewPage.value = 1 }
  }
  function togglePdf(id) {
    const s = new Set(selectedPdfIds.value)
    s.has(id) ? s.delete(id) : s.add(id)
    selectedPdfIds.value = [...s]
  }

  // ---------- preview (debounce) ----------
  let _t = null
  function schedulePreview() {
    if (_t) clearTimeout(_t)
    _t = setTimeout(refreshPreview, 250)
  }
  async function refreshPreview() {
    if (!canPreview.value) { if (previewUrl.value) { URL.revokeObjectURL(previewUrl.value); previewUrl.value = null } return }
    status.previewLoading = true
    status.error = null
    try {
      const resp = await api.post('/api/preview', {
        pdf_id: previewPdfId.value,
        logo_id: selectedLogoId.value,
        page_index: previewPage.value,
        copy_number: Math.min(Math.max(1, Number(previewCopy.value) || 1), 200),
        options: _payload(),
      }, { responseType: 'blob' })
      if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
      previewUrl.value = URL.createObjectURL(resp.data)
    } catch (e) {
      const isBlobErr = e.response && e.response.data instanceof Blob
      status.error = isBlobErr ? await e.response.data.text() : (e.message || 'preview ล้มเหลว')
    } finally {
      status.previewLoading = false
    }
  }

  // ---------- stamp ----------
  async function stampAll() {
    if (!selectedLogoId.value || !targetsToStamp.value.length) return
    status.stamping = true
    status.error = null
    try {
      const resp = await api.post('/api/stamp', {
        pdf_ids: targetsToStamp.value,
        logo_id: selectedLogoId.value,
        options: _payload(),
      }, { responseType: 'blob' })
      const cd = resp.headers['content-disposition'] || ''
      let filename = null
      const star = cd.match(/filename\*=UTF-8''([^;]+)/i)
      if (star) { try { filename = decodeURIComponent(star[1]) } catch { /* fallback */ } }
      if (!filename) {
        const m = cd.match(/filename="?([^";]+)"?/i)
        if (m) filename = m[1]
      }
      if (!filename) filename = (resp.data.type === 'application/zip' ? 'stamped_logos.zip' : 'stamped.pdf')
      const url = URL.createObjectURL(resp.data)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a); a.click(); a.remove()
      setTimeout(() => URL.revokeObjectURL(url), 4000)
      status.notice = `ดาวน์โหลด "${filename}" สำเร็จ (${targetsToStamp.value.length} ไฟล์)`
    } catch (e) {
      const isBlobErr = e.response && e.response.data instanceof Blob
      status.error = isBlobErr ? await e.response.data.text() : (e.message || 'stamp ล้มเหลว')
    } finally {
      status.stamping = false
    }
  }

  async function loadFonts() {
    try {
      const { data } = await api.get('/api/fonts')
      if (Array.isArray(data) && data.length) {
        fonts.value = data
        if (!data.includes(options.text_font)) options.text_font = data.includes('Helvetica-Bold') ? 'Helvetica-Bold' : data[0]
      }
    } catch { /* ใช้ค่า default ต่อไป */ }
  }

  // ---------- presets (ชุดการตั้งค่าที่บันทึกไว้) ----------
  const LS_KEY = 'pls.last-config.v1'
  let _ready = false   // gate: ห้าม persist ก่อน restore จบ — ไม่งั้น watch ตอน init เขียน default ทับของจริง

  function _persistLocal() {
    if (!_ready) return
    try {
      localStorage.setItem(LS_KEY, JSON.stringify({
        options: { ...options }, selectedLogoId: selectedLogoId.value,
        editingPresetId: editingPresetId.value,
      }))
    } catch { /* storage เต็ม/privacy mode — ไม่ fatal */ }
  }

  function _restoreLocal() {
    try {
      const raw = localStorage.getItem(LS_KEY)
      if (!raw) return
      const saved = JSON.parse(raw)
      if (saved.options && typeof saved.options === 'object') {
        for (const k of Object.keys(options)) {
          if (k in saved.options && saved.options[k] !== null && saved.options[k] !== undefined) options[k] = saved.options[k]
          else if (k in saved.options && saved.options[k] === null) options[k] = null
        }
      }
      if (saved.selectedLogoId && logos.value.some((l) => l.id === saved.selectedLogoId)) {
        selectedLogoId.value = saved.selectedLogoId
        editingPresetId.value = saved.editingPresetId ?? null
      }
    } catch { /* config เก่าพัง — ใช้ default */ }
  }

  async function loadPresets() {
    try {
      const { data } = await api.get('/api/presets')
      presets.value = Array.isArray(data) ? data : []
    } catch { presets.value = [] }
  }

  async function savePreset(name) {
    const body = { name: (name || '').trim() || 'งานของฉัน', logo_id: selectedLogoId.value, options: _payload() }
    if (editingPresetId.value) body.id = editingPresetId.value
    const { data } = await api.post('/api/presets', body)
    const i = presets.value.findIndex((p) => p.id === data.id)
    if (i >= 0) presets.value[i] = data; else presets.value.unshift(data)
    editingPresetId.value = data.id
    status.notice = `บันทึก "${data.name}" แล้ว — คราวหน้าคลิกใช้ได้เลย`
    return data
  }

  function applyPreset(id) {
    const p = presets.value.find((x) => x.id === id)
    if (!p) return
    Object.assign(options, p.options)
    if (p.options.page_scope && /^[\d,\-\s]+$/.test(p.options.page_scope)) {
      options.page_scope = 'custom'; options.custom_pages = p.options.page_scope
    } else if (['all', 'first'].includes(p.options.page_scope)) {
      options.custom_pages = ''
    }
    const logoGone = p.logo_id && !logos.value.some((l) => l.id === p.logo_id)
    if (p.logo_id && !logoGone) selectedLogoId.value = p.logo_id
    editingPresetId.value = p.id
    status.notice = logoGone
      ? `ใช้ "${p.name}" — ⚠ โลโก้ของงานนี้ถูกลบไปแล้ว เลือกโลโก้ใหม่ก่อน stamp`
      : `ใช้ชุดตั้งค่า "${p.name}" แล้ว`
    schedulePreview()
  }

  function newConfig() {
    editingPresetId.value = null
    status.notice = 'โหมดค่าตั้งใหม่ (บันทึกจะไม่ทับ preset ใด)'
  }

  async function deletePreset(id) {
    await api.delete(`/api/presets/${id}`)
    presets.value = presets.value.filter((p) => p.id !== id)
    if (editingPresetId.value === id) editingPresetId.value = null
  }

  // ทุกการแก้ options/config = auto-save ลง localStorage (กัน reload แล้วหาย)
  watch(options, _persistLocal, { deep: true })
  watch([selectedLogoId, editingPresetId], _persistLocal)

  async function init() {
    await Promise.all([loadLogos(), loadPdfs(), loadFonts(), loadPresets()])
    _restoreLocal()
    _ready = true   // เปิด persist ก็ต่อเมื่ออ่านค่าเก่าเสร็จแล้ว
    schedulePreview()
  }

  return {
    logos, pdfs, fonts, presets, editingPresetId,
    selectedLogoId, selectedPdfIds, previewPdfId, previewPage, previewUrl, previewCopy,
    status, options, selectedLogo, previewPdf, canPreview, targetsToStamp, totalOutputs,
    loadLogos, uploadLogo, deleteLogo, loadPdfs, uploadPdfs, removePdf, togglePdf,
    schedulePreview, refreshPreview, stampAll, init,
    savePreset, applyPreset, deletePreset, newConfig,
  }
})
