<script setup>
import { ref } from 'vue'
import { useStamper } from '../stores/stamper'

const store = useStamper()
const dragging = ref(false)

function fmtSize(b) {
  if (b < 1024) return b + ' B'
  if (b < 1024 * 1024) return (b / 1024).toFixed(0) + ' KB'
  return (b / 1048576).toFixed(1) + ' MB'
}
async function onFiles(files) {
  const pdfs = [...files].filter((f) => /\.pdf$/i.test(f.name))
  if (!pdfs.length) { store.status.error = 'รับเฉพาะไฟล์ .pdf'; return }
  try { await store.uploadPdfs(pdfs) } catch (e) { store.status.error = e.message }
}
function pick(e) { onFiles(e.target.files); e.target.value = '' }
function selectForPreview(id) { store.previewPdfId = id; store.previewPage = 1; store.schedulePreview() }
</script>

<template>
  <section class="card p-4">
    <div class="mb-3 flex items-center justify-between">
      <h2 class="text-sm font-bold uppercase tracking-wide text-forest-700">2 · ไฟล์ PDF</h2>
      <span class="text-xs text-forest-500">{{ store.pdfs.length }} ไฟล์</span>
    </div>

    <label
      class="flex cursor-pointer flex-col items-center justify-center gap-1 rounded-xl border-2 border-dashed px-4 py-5 text-center transition"
      :class="dragging ? 'border-forest-500 bg-forest-50' : 'border-forest-200 hover:border-forest-300 hover:bg-forest-50/50'"
      @dragover.prevent="dragging = true" @dragleave.prevent="dragging = false"
      @drop.prevent="dragging = false; onFiles($event.dataTransfer.files)"
    >
      <input type="file" accept="application/pdf,.pdf" multiple class="hidden" @change="pick" />
      <svg class="h-6 w-6 text-forest-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M14 3v5h5"/><path d="M14 3H6a2 2 0 00-2 2v14a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M9 15h6M9 12h3"/></svg>
      <span class="text-sm font-medium text-forest-700">ลากไฟล์ PDF มาวาง หรือคลิกเลือก</span>
      <span class="text-[11px] text-forest-400">เพิ่มได้หลายไฟล์พร้อมกัน</span>
    </label>

    <ul v-if="store.pdfs.length" class="mt-3 divide-y divide-forest-100">
      <li v-for="p in store.pdfs" :key="p.id"
        class="flex items-center gap-2 py-2"
        :class="store.previewPdfId === p.id ? 'bg-forest-50/60' : ''">
        <input type="checkbox" class="h-4 w-4 accent-forest-700" :checked="store.selectedPdfIds.includes(p.id)"
          @change="store.togglePdf(p.id)" title="รวมไฟล์นี้ใน Stamp" />
        <button class="flex-1 truncate text-left text-sm font-medium text-forest-800 hover:text-forest-600"
          @click="selectForPreview(p.id)" :title="p.filename">{{ p.filename }}</button>
        <span class="shrink-0 rounded bg-ivory-200 px-1.5 py-0.5 text-[11px] text-forest-600">{{ p.page_count }} หน้า</span>
        <span class="hidden shrink-0 text-[11px] text-forest-400 sm:inline">{{ fmtSize(p.size_bytes) }}</span>
        <button class="shrink-0 text-forest-400 hover:text-red-500" @click="store.removePdf(p.id)" title="ลบ">
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 6l12 12M18 6L6 18"/></svg>
        </button>
      </li>
    </ul>
    <p v-else class="mt-3 text-center text-xs text-forest-400">ยังไม่มีไฟล์ — คลิกชื่อไฟล์เพื่อดู preview</p>
  </section>
</template>
