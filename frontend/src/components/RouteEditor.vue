<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { api } from '../api'
import type { Estimate, Route, RouteInput, Stop } from '../types'
import RouteMap from './RouteMap.vue'

const props = defineProps<{ route: Route | null }>()
const emit = defineEmits<{ saved: [Route]; deleted: [string] }>()
const form = reactive<RouteInput>({ name: '', average_speed_kmh: 30, stops: [] })
const estimate = ref<Estimate | null>(null)
const error = ref('')
const selectedIndex = ref(0)
let timer: number | undefined

const canSave = computed(() => form.name.trim() && form.average_speed_kmh > 0)
const secondsText = (seconds: number) => `${Math.floor(seconds / 60)}분 ${seconds % 60}초`
const distanceText = (meters: number) => meters >= 1000 ? `${(meters / 1000).toFixed(1)}km` : `${meters}m`
const emptyStop = (): Stop => ({ name: '', distance_from_previous_m: 0, latitude: null, longitude: null })

function reset(route: Route | null) {
  Object.assign(form, route ? { name: route.name, average_speed_kmh: route.average_speed_kmh, stops: route.stops.map(({ segment_seconds, cumulative_seconds, ...stop }) => stop) } : { name: '', average_speed_kmh: 30, stops: [] })
  selectedIndex.value = 0
  error.value = ''
}

function addStop() {
  form.stops.push(emptyStop())
  selectedIndex.value = form.stops.length - 1
}

function removeStop(index: number) {
  form.stops.splice(index, 1)
  selectedIndex.value = Math.max(0, index - 1)
}

function moveStop(index: number, direction: number) {
  const target = index + direction
  if (target < 0 || target >= form.stops.length) return
  ;[form.stops[index], form.stops[target]] = [form.stops[target], form.stops[index]]
  selectedIndex.value = target
}

function setCoordinate(latitude: number, longitude: number) {
  const stop = form.stops[selectedIndex.value]
  if (stop) Object.assign(stop, { latitude, longitude })
}

function setPlace(name: string, latitude: number, longitude: number) {
  const stop = form.stops[selectedIndex.value]
  if (stop) Object.assign(stop, { name, latitude, longitude })
}

async function save() {
  if (!canSave.value) return
  try {
    const saved = props.route ? await api.updateRoute(props.route.id, form) : await api.createRoute(form)
    emit('saved', saved)
  }
  catch (cause) { error.value = cause instanceof Error ? cause.message : '저장에 실패했습니다.' }
}

async function remove() {
  if (props.route && confirm(`'${props.route.name}' 노선을 삭제할까요?`)) {
    await api.deleteRoute(props.route.id)
    emit('deleted', props.route.id)
  }
}

watch(() => props.route, reset, { immediate: true })
watch(form, () => {
  clearTimeout(timer)
  if (!canSave.value) return
  timer = window.setTimeout(async () => { try { estimate.value = await api.estimate(form) } catch { estimate.value = null } }, 300)
}, { deep: true })
</script>

<template>
  <section class="editor">
    <header><h2>{{ route ? '노선 편집' : '새 노선' }}</h2><button v-if="route" class="danger" @click="remove">삭제</button></header>
    <label>노선 이름<input v-model.trim="form.name" placeholder="예: 마을버스 01" /></label>
    <label>평균 속도 (km/h)<input v-model.number="form.average_speed_kmh" type="number" min="1" max="120" /></label>
    <div class="summary"><span>총 거리 {{ distanceText(estimate?.total_distance_m ?? 0) }}</span><strong>예상 {{ secondsText(estimate?.total_seconds ?? 0) }}</strong></div>
    <RouteMap :stops="form.stops" :selected-index="selectedIndex" @coordinate="setCoordinate" @place="setPlace" />
    <p class="hint">정류장을 선택한 뒤 지도에서 클릭하거나 장소 검색 결과를 고르면 좌표가 입력됩니다.</p>
    <div class="stops"><header><h3>정류장</h3><button @click="addStop">+ 정류장 추가</button></header>
      <article v-for="(stop, index) in form.stops" :key="index" :class="{ selected: index === selectedIndex }" @click="selectedIndex = index">
        <b>{{ index + 1 }}</b><input v-model.trim="stop.name" placeholder="정류장 이름" />
        <label>이전 거리(m)<input v-model.number="stop.distance_from_previous_m" type="number" min="0" :disabled="index === 0" /></label>
        <span>{{ secondsText(estimate?.stops[index]?.segment_seconds ?? 0) }}</span>
        <button :disabled="index === 0" @click.stop="moveStop(index, -1)">↑</button><button :disabled="index === form.stops.length - 1" @click.stop="moveStop(index, 1)">↓</button><button class="danger" @click.stop="removeStop(index)">×</button>
      </article>
    </div>
    <p v-if="error" class="error">{{ error }}</p><button class="save" :disabled="!canSave" @click="save">저장</button>
  </section>
</template>
