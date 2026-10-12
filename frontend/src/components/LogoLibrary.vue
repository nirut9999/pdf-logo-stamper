<script setup>
import { ref } from 'vue'
import { useStamper } from '../stores/stamper'

const store = useStamper()
const input = ref(null)
const dragging = ref(false)

async function onFiles(files) {
  for (const f of files) {
    if (!/\.(png|jpe?g|webp)$/i.test(f.name)) continue
    try { await store.uploadLogo(f) } catch (e) { store.status.error = e.message }
  }
}
function pick(e) { onFiles([...e.target.files]) ; e.target.value = '' }
</script>

<template>
  <section class="card p-4">
    <div class="mb-3 flex items-center justify-between">
      <h2 class="text-sm font-bold uppercase tracking-wide text-forest-700">1 · คลังโลโก้</h2>
      <span class="text-xs text-forest-500">{{ store.logos.length }} รายการ</span>
    </div>

    <label
      class="flex cursor-pointer flex-col items-center justify-center gap-1 rounded-xl border-2 border-dashed px-4 py-5 text-center transition"
      :class="dragging ? 'border-forest-500 bg-forest-50' : 'border-forest-200 hover:border-forest-300 hover:bg-forest-50/50'"
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop.prevent="dragging = false; onFiles([...$event.dataTransfer.files])"
    >
      <input ref="input" type="file" accept="image/png,image/jpeg,image/webp" multiple class="hidden" @change="pick" />
      <svg class="h-6 w-6 text-forest-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 16V4m0 0L8 8m4-4 4 4"/><path d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2"/></svg>
      <span class="text-sm font-medium text-forest-700">ลากมาวาง หรือคลิกเพื่ออัปโหลด</span>
      <span class="text-[11px] text-forest-400">PNG (รองรับพื้นโปร่งใส) / JPG / WEBP</span>
    </label>

    <div v-if="store.logos.length" class="mt-4 grid grid-cols-3 gap-2">
      <button
        v-for="l in store.logos" :key="l.id"
        @click="store.selectedLogoId = l.id; store.schedulePreview()"
        class="group relative flex aspect-video items-center justify-center rounded-lg border bg-ivory-50 p-1.5 transition"
        :class="store.selectedLogoId === l.id ? 'border-forest-600 ring-2 ring-forest-400' : 'border-forest-100 hover:border-forest-300'"
        :title="l.filename"
      >
        <img :src="l.url" :alt="l.filename" class="max-h-full max-w-full object-contain" />
        <span
          @click.stop="store.deleteLogo(l.id)"
          class="absolute -right-1.5 -top-1.5 hidden h-5 w-5 place-items-center rounded-full bg-red-500 text-[11px] text-white group-hover:grid"
        >×</span>
      </button>
    </div>
  </section>
</template>
