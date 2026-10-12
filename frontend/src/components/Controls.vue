<script setup>
import { computed } from 'vue'
import { useStamper } from '../stores/stamper'
const store = useStamper()
const o = store.options

function changed() { store.schedulePreview() }

const THAI_RE = /[\u0E00-\u0E7F]/
const needsThaiFont = computed(() =>
  o.include_text && THAI_RE.test(o.text_template || '') && !/sarabun/i.test(o.text_font || ''))

function fontLabel(f) {
  const map = { 'Sarabun': 'Sarabun (ไทย/regular)', 'Sarabun-Bold': 'Sarabun Bold (ไทย)' }
  return map[f] || f + ' (ลาตินเท่านั้น)'
}
function usePreset(tmpl, font) {
  o.text_template = tmpl
  if (font && store.fonts.includes(font)) o.text_font = font
  changed()
}
</script>

<template>
  <section class="card p-4">
    <h2 class="mb-3 text-sm font-bold uppercase tracking-wide text-forest-700">3 · การจัดวาง Watermark</h2>

    <div class="space-y-4">
      <!-- ขนาด / ระยะขอบ -->
      <div>
        <div class="flex items-baseline justify-between">
          <label class="label !mb-0">ขนาดโลโก้ (ย่อ–ขยาย)</label>
          <span class="text-sm font-semibold tabular-nums text-forest-800">{{ o.logo_width_mm }} mm</span>
        </div>
        <input class="range mt-1" type="range" min="5" max="120" step="1" v-model.number="o.logo_width_mm" @input="changed" />
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <div class="flex items-baseline justify-between">
            <label class="label !mb-0">ระยะขอบบน</label>
            <span class="text-sm font-semibold tabular-nums text-forest-800">{{ o.margin_top_mm }} mm</span>
          </div>
          <input class="range mt-1" type="range" min="0" max="40" step="1" v-model.number="o.margin_top_mm" @input="changed" />
        </div>
        <div>
          <div class="flex items-baseline justify-between">
            <label class="label !mb-0">ระยะขอบขวา</label>
            <span class="text-sm font-semibold tabular-nums text-forest-800">{{ o.margin_right_mm }} mm</span>
          </div>
          <input class="range mt-1" type="range" min="0" max="40" step="1" v-model.number="o.margin_right_mm" @input="changed" />
        </div>
      </div>

      <!-- ความจาง + เอียง -->
      <div class="grid grid-cols-2 gap-3">
        <div>
          <div class="flex items-baseline justify-between">
            <label class="label !mb-0">ความจาง (มองทะลุ)</label>
            <span class="text-sm font-semibold tabular-nums text-forest-800">{{ Math.round(o.opacity * 100) }}%</span>
          </div>
          <input class="range mt-1" type="range" min="0.05" max="1" step="0.05" v-model.number="o.opacity" @input="changed" />
        </div>
        <div>
          <div class="flex items-baseline justify-between">
            <label class="label !mb-0">เอียง</label>
            <span class="text-sm font-semibold tabular-nums text-forest-800">{{ o.rotation_degrees }}°</span>
          </div>
          <input class="range mt-1" type="range" min="-90" max="90" step="1" v-model.number="o.rotation_degrees" @input="changed" />
        </div>
      </div>
      <div class="-mt-1 flex gap-1">
        <button v-for="d in [-45, -15, 0, 15, 45]" :key="d" @click="o.rotation_degrees = d; changed()"
          class="rounded-md border border-forest-100 bg-ivory-50 px-2 py-0.5 text-[11px] text-forest-600 hover:border-forest-300"
          :class="o.rotation_degrees === d ? '!border-forest-500 bg-forest-50 font-semibold' : ''">{{ d }}°</button>
        <span class="ml-auto self-center text-[10px] text-forest-400">+ = เอนตามเข็ม</span>
      </div>

      <!-- ข้อความ COPY No.N (วางข้างโลโก้ ทางขวา) -->
      <div class="rounded-xl border border-forest-100 bg-ivory-50 p-3">
        <label class="flex cursor-pointer items-center gap-2 text-sm font-semibold text-forest-800">
          <input type="checkbox" class="h-4 w-4 accent-forest-700" v-model="o.include_text" @change="changed" />
          วางข้อความข้างโลโก้ → (default สีแดง)
        </label>
        <div v-if="o.include_text" class="mt-3 space-y-3">
          <div>
            <label class="label">ข้อความ ({n} = เลขสำเนา)</label>
            <div class="flex gap-2">
              <input v-model="o.text_template" @input="changed"
                class="w-full rounded-lg border border-forest-200 px-3 py-1.5 text-sm focus:border-forest-500 focus:outline-none focus:ring-1 focus:ring-forest-400"
                placeholder="COPY No.{n}" />
              <input type="color" v-model="o.text_color" @input="changed"
                class="h-9 w-10 shrink-0 cursor-pointer rounded border border-forest-200 bg-white p-0.5" title="สีข้อความ" />
            </div>
            <div class="mt-1.5 flex gap-1">
              <button @click="usePreset('COPY No.{n}', 'Helvetica-Bold')" class="rounded-md border border-forest-100 bg-white px-2 py-0.5 text-[11px] text-forest-600 hover:border-forest-300">COPY No.{n}</button>
              <button @click="usePreset('ฉบับที่ {n}', 'Sarabun-Bold')" class="rounded-md border border-forest-100 bg-white px-2 py-0.5 text-[11px] text-forest-600 hover:border-forest-300">ฉบับที่ {n} (Sarabun)</button>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="label">Font ข้อความ</label>
              <select v-model="o.text_font" @change="changed"
                class="w-full rounded-lg border border-forest-200 bg-white px-2 py-1.5 text-sm focus:border-forest-500 focus:outline-none">
                <option v-for="f in store.fonts" :key="f" :value="f">{{ fontLabel(f) }}</option>
              </select>
            </div>
            <div>
              <div class="flex items-baseline justify-between">
                <label class="label !mb-0">ขนาดข้อความ</label>
                <span class="text-xs font-semibold tabular-nums text-forest-800">{{ o.text_size_mm || 'auto' }} mm</span>
              </div>
              <input class="range mt-1.5" type="range" min="2" max="30" step="0.5" v-model.number="o.text_size_mm" @input="changed" />
            </div>
          </div>
          <p v-if="needsThaiFont" class="rounded-md bg-amber-50 px-2 py-1 text-[11px] text-amber-700">
            ข้อความมีตัวไทย — เลือก font ไทย (Sarabun) ถึงจะไม่ว่าง
          </p>
        </div>
      </div>

      <!-- จำนวนสำเนา -->
      <div>
        <div class="flex items-baseline justify-between">
          <label class="label !mb-0">จำนวนสำเนา (copies)</label>
          <span class="text-sm font-semibold tabular-nums text-forest-800">{{ o.copies }} ชุด</span>
        </div>
        <input class="range mt-1" type="range" min="1" max="200" step="1" v-model.number="o.copies" @input="changed" />
        <div class="mt-1.5 flex gap-1">
          <button v-for="c in [1, 10, 50, 100, 200]" :key="c" @click="o.copies = c; changed()"
            class="rounded-md border border-forest-100 bg-white px-2 py-0.5 text-[11px] text-forest-600 hover:border-forest-300"
            :class="o.copies === c ? '!border-forest-500 bg-forest-50 font-semibold' : ''">{{ c }}</button>
          <span class="ml-auto self-center text-[10px] text-forest-400">เลข 1..N ต่อไฟล์ · หลายไฟล์ส่งเป็น ZIP</span>
        </div>
      </div>

      <!-- ขอบเขตหน้า -->
      <div>
        <label class="label">วางบนหน้า</label>
        <div class="grid grid-cols-3 gap-1 rounded-lg bg-ivory-200 p-1 text-sm">
          <button v-for="s in [['all','ทุกหน้า'],['first','หน้าแรก'],['custom','กำหนดเอง']]" :key="s[0]"
            @click="o.page_scope = s[0]; changed()"
            class="rounded-md px-2 py-1.5 font-medium transition"
            :class="o.page_scope === s[0] ? 'bg-forest-700 text-ivory-50 shadow' : 'text-forest-600 hover:bg-white'">
            {{ s[1] }}
          </button>
        </div>
        <input v-if="o.page_scope === 'custom'" v-model="o.custom_pages" @input="changed"
          placeholder="เช่น 1-3,5,8- (1-based)"
          class="mt-2 w-full rounded-lg border border-forest-200 px-3 py-2 text-sm focus:border-forest-500 focus:outline-none focus:ring-1 focus:ring-forest-400" />
      </div>

      <details class="rounded-lg border border-forest-100 bg-ivory-50 p-2.5 text-sm">
        <summary class="cursor-pointer font-medium text-forest-700">ขั้นสูง: บังคับความสูงโลโก้ (ไม่คงสัดส่วน)</summary>
        <div class="mt-2 flex items-center gap-3">
          <input type="checkbox" class="h-4 w-4 accent-forest-700" :checked="o.logo_height_mm != null"
            @change="o.logo_height_mm = $event.target.checked ? 15 : null; changed()" />
          <label v-if="o.logo_height_mm != null" class="flex flex-1 items-center gap-2 text-xs">
            สูง
            <input class="range" type="range" min="3" max="120" step="1" v-model.number="o.logo_height_mm" @input="changed" />
            {{ o.logo_height_mm }} mm
          </label>
        </div>
      </details>
    </div>
  </section>
</template>
