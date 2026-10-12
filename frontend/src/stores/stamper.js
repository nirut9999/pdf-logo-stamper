import { defineStore } from 'pinia'
import { ref, reactive, computed } from 'vue'
import api from '../api/api'

// Store เดียวที่เป็น source of truth — component ห้ามเรียก axios ตรงๆ
export const useStamper = defineStore('stamper', () => {
  const logos = ref([])
  const pdfs = ref([])
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
    include_text: true,     // ข้อความใต้โลโก้
    text_template: 'COPY No.{n}',
    text_color: '#CC0000',
    text_size_mm: null,     // null = auto
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
      const m = cd.match(/filename="?(.+?)"?$/i)
      const filename = m ? m[1] : (resp.data.type === 'application/zip' ? 'stamped_logos.zip' : 'stamped.pdf')
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

  async function init() {
    await Promise.all([loadLogos(), loadPdfs()])
    schedulePreview()
  }

  return {
    logos, pdfs, selectedLogoId, selectedPdfIds, previewPdfId, previewPage, previewUrl, previewCopy,
    status, options, selectedLogo, previewPdf, canPreview, targetsToStamp, totalOutputs,
    loadLogos, uploadLogo, deleteLogo, loadPdfs, uploadPdfs, removePdf, togglePdf,
    schedulePreview, refreshPreview, stampAll, init,
  }
})
