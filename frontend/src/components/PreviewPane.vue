<script setup>
import { useStamper } from '../stores/stamper'
const store = useStamper()

function goto(n) {
  const max = store.previewPdf?.page_count || 1
  store.previewPage = Math.min(max, Math.max(1, n))
  store.schedulePreview()
}
</script>

<template>
  <section class="card sticky top-6 flex min-h-[70vh] flex-col overflow-hidden">
    <div class="flex items-center justify-between border-b border-forest-100 px-4 py-3">
      <h2 class="text-sm font-bold uppercase tracking-wide text-forest-700">Preview (ตรงกับไฟล์จริง)</h2>
      <div v-if="store.previewPdf" class="flex items-center gap-2 text-sm">
        <label class="flex items-center gap-1 text-xs text-forest-600">เลขสำเนาตัวอย่าง
          <input type="number" min="1" :max="store.options.copies" v-model.number="store.previewCopy"
            @change="store.schedulePreview()"
            class="w-16 rounded-md border border-forest-200 px-2 py-1 text-sm tabular-nums focus:border-forest-500 focus:outline-none" />
        </label>
        <button class="btn-ghost !px-2 !py-1" :disabled="store.previewPage <= 1" @click="goto(store.previewPage - 1)">◀</button>
        <span class="tabular-nums text-forest-700">หน้า {{ store.previewPage }} / {{ store.previewPdf.page_count }}</span>
        <button class="btn-ghost !px-2 !py-1" :disabled="store.previewPage >= store.previewPdf.page_count" @click="goto(store.previewPage + 1)">▶</button>
      </div>
    </div>

    <div class="relative flex-1 bg-ivory-200/40">
      <!-- ไม่มีข้อมูล -->
      <div v-if="!store.canPreview" class="grid h-full place-items-center p-6 text-center">
        <div class="text-forest-400">
          <svg class="mx-auto mb-3 h-12 w-12 opacity-60" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
          <p class="text-sm font-medium">เลือกโลโก้และอัปโหลดไฟล์ PDF<br/>เพื่อดู preview การวางมุมขวาบน</p>
        </div>
      </div>

      <!-- ภาพ preview -->
      <div v-else class="grid h-full place-items-center overflow-auto p-4">
        <img v-if="store.previewUrl" :src="store.previewUrl" alt="preview"
          class="max-h-[75vh] rounded-lg bg-white shadow-card ring-1 ring-forest-100" />
        <p v-if="!store.previewUrl && !store.status.previewLoading" class="text-sm text-forest-400">กำลังเตรียมภาพ…</p>
      </div>

      <!-- overlay โหลด -->
      <div v-if="store.status.previewLoading" class="absolute inset-0 grid place-items-center bg-ivory-100/60 backdrop-blur-[1px]">
        <div class="flex items-center gap-2 rounded-lg bg-white/90 px-3 py-2 text-sm text-forest-700 shadow">
          <svg class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"/></svg>
          กำลังคำนวณ…
        </div>
      </div>
    </div>

    <div class="border-t border-forest-100 px-4 py-2 text-[11px] text-forest-500">
      ภาพนี้สร้างจาก engine เดียวกับที่ใช้ตอน Stamp จริง — เห็นใน preview คือที่ได้ในไฟล์
    </div>
  </section>
</template>
