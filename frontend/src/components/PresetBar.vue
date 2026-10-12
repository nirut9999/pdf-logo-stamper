<script setup>
import { ref } from 'vue'
import { useStamper } from '../stores/stamper'

const store = useStamper()
const nameInput = ref('')
const saving = ref(false)

async function save() {
  saving.value = true
  try {
    const target = store.editingPresetId
      ? store.presets.find((p) => p.id === store.editingPresetId)
      : null
    const name = (nameInput.value || '').trim() || (target ? target.name : 'งานของฉัน')
    await store.savePreset(name)
    nameInput.value = ''
  } catch (e) {
    store.status.error = typeof e?.response?.data === 'string' ? e.response.data
      : (e?.response?.data?.detail ? (Array.isArray(e.response.data.detail) ? 'ค่าตั้งไม่valid — ตรวจ font/ข้อความ' : e.response.data.detail) : (e.message || 'บันทึกไม่สำเร็จ'))
  } finally {
    saving.value = false
  }
}
function editName(id) {
  const p = store.presets.find((x) => x.id === id)
  return p ? p.name : ''
}
</script>

<template>
  <section class="card p-4">
    <div class="mb-3 flex items-center justify-between">
      <h2 class="text-sm font-bold uppercase tracking-wide text-forest-700">งานที่บันทึกไว้</h2>
      <button v-if="store.editingPresetId" @click="store.newConfig()" class="btn-ghost !px-2 !py-1 text-xs">
        + ค่าตั้งใหม่
      </button>
    </div>

    <div v-if="store.presets.length" class="flex flex-wrap gap-1.5">
      <button
        v-for="p in store.presets" :key="p.id"
        @click="store.applyPreset(p.id)"
        class="group inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm transition"
        :class="store.editingPresetId === p.id
          ? 'border-forest-600 bg-forest-700 text-ivory-50 shadow'
          : 'border-forest-200 bg-ivory-50 text-forest-700 hover:border-forest-400 hover:bg-forest-50'"
        :title="`${p.name} · โลโก้ ${p.options.logo_width_mm}mm · ${p.options.copies || 1} สำเนา ·อัปเดต ${p.updated_at?.slice(0, 10) || ''}`"
      >
        <span class="max-w-[180px] truncate font-medium">{{ p.name }}</span>
        <span
          @click.stop="store.deletePreset(p.id)"
          class="hidden h-4 w-4 shrink-0 place-items-center rounded-full text-[10px] leading-none group-hover:grid"
          :class="store.editingPresetId === p.id ? 'bg-forest-500/60 text-ivory-50 hover:bg-red-400' : 'bg-forest-100 text-forest-500 hover:bg-red-100 hover:text-red-600'"
          title="ลบชุดตั้งค่านี้ออก"
        >×</span>
      </button>
    </div>
    <p v-else class="text-xs text-forest-400">
      ยังไม่มีการตั้งค่า — ตั้งค่างานเดิมแล้วกด "บันทึก" ครั้งเดียว ครั้งหน้าคลิกชื่องานจากตรงนี้ได้เลย
    </p>

    <div class="mt-3 flex gap-2">
      <input v-model="nameInput" @keyup.enter="save()"
        :placeholder="store.editingPresetId ? `ทับของเดิม: “${editName(store.editingPresetId)}” (เว้นว่าง = ทับ)` : 'ตั้งชื่องาน เช่น สัญญาเช่า 2569'"
        class="w-full rounded-lg border border-forest-200 px-3 py-1.5 text-sm focus:border-forest-500 focus:outline-none focus:ring-1 focus:ring-forest-400" />
      <button @click="save()" :disabled="saving"
        class="btn-ghost shrink-0 text-sm" :class="store.editingPresetId ? '!border-brass-400 !text-forest-900 hover:!bg-brass-50' : ''">
        {{ saving ? 'บันทึก…' : store.editingPresetId ? '💾 ทับของเดิม' : '💾 บันทึก' }}
      </button>
    </div>
  </section>
</template>
