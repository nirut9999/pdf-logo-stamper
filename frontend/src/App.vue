<script setup>
import { onMounted } from 'vue'
import { useStamper } from './stores/stamper'
import LogoLibrary from './components/LogoLibrary.vue'
import PdfList from './components/PdfList.vue'
import Controls from './components/Controls.vue'
import PreviewPane from './components/PreviewPane.vue'

const store = useStamper()
onMounted(() => store.init())
</script>

<template>
  <div class="min-h-screen">
    <header class="bg-forest-800 text-ivory-50">
      <div class="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-5 py-4">
        <div class="flex items-center gap-3">
          <div class="grid h-11 w-11 place-items-center rounded-xl bg-brass-400/90 font-bold text-forest-900">
            PLS
          </div>
          <div>
            <h1 class="text-lg font-bold leading-tight">PDF Logo Stamper</h1>
            <p class="text-xs text-forest-100/80">โลโก้ + ข้อความ COPY No.N มุมขวาบนทุกหน้า · ย่อ/ขยาย/เอียง/ความจาง · N สำเนาต่อไฟล์</p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <button
            class="btn-primary !bg-brass-400 !text-forest-900 hover:!bg-brass-300"
            :disabled="store.status.stamping || !store.canPreview || !store.targetsToStamp.length"
            @click="store.stampAll()"
          >
            <svg v-if="store.status.stamping" class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"/></svg>
            <span>{{ store.status.stamping ? 'กำลังวาง watermark…' : `Stamp & ดาวน์โหลด (${store.targetsToStamp.length} ไฟล์ × ${store.options.copies} สำเนา = ${store.totalOutputs})` }}</span>
          </button>
        </div>
      </div>
    </header>

    <div v-if="store.status.error" class="mx-auto mt-4 max-w-7xl px-5">
      <div class="rounded-lg border border-red-200 bg-red-50 px-4 py-2.5 text-sm text-red-700">
        {{ store.status.error }}
      </div>
    </div>

    <main class="mx-auto grid max-w-7xl grid-cols-1 gap-6 px-5 py-6 lg:grid-cols-[minmax(320px,380px)_minmax(0,1fr)]">
      <div class="flex flex-col gap-5">
        <LogoLibrary />
        <PdfList />
        <Controls />
      </div>
      <PreviewPane />
    </main>

    <footer class="mx-auto max-w-7xl px-5 pb-8 pt-2 text-center text-xs text-forest-500">
      ประมวลผลบนเซิร์ฟเวอร์ของคุณเอง · ไฟล์ไม่ถูกส่งออกไปภายนอก
    </footer>
  </div>
</template>
