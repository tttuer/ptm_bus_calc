<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { api } from '../api'
import type { GenerationSettings, Schedule, ScheduleInput, Trip } from '../types'

const props = defineProps<{ schedule: Schedule | null }>()
const emit = defineEmits<{ saved: [Schedule]; deleted: [string] }>()
const tab = ref<'matrix' | 'all' | 'timeline'>('matrix')
const error = ref('')
const message = ref('')
const emptyGeneration = (): GenerationSettings => ({ first_departure: '06:00', last_departure: '23:00', outbound_minutes: 60, inbound_minutes: 60, min_rest_minutes: 10, bus_count: 5, interval_minutes: 0 })
const emptySchedule = (): ScheduleInput => ({ name: '새 노선', origin: '기점', destination: '종점', max_average_speed_kmh: 60, headway_minutes: 0, generation: emptyGeneration(), stops: [], buses: [], drivers: [], trips: [], activities: [] })
const form = reactive<ScheduleInput>(emptySchedule())
const canGenerate = computed(() => form.name && form.origin && form.destination)
const sortedTrips = computed(() => [...form.trips].sort((a, b) => a.departure_time.localeCompare(b.departure_time)))
const vehicleRows = computed(() => form.buses.map(bus => ({ bus, trips: form.trips.filter(trip => trip.bus_id === bus.id).sort((a, b) => a.departure_time.localeCompare(b.departure_time)) })))
const rounds = computed(() => Math.max(1, ...vehicleRows.value.map(row => Math.ceil(row.trips.length / 2))))
const totalTrips = computed(() => form.trips.length / 2)
const averageRounds = computed(() => form.buses.length ? (totalTrips.value / form.buses.length).toFixed(1) : '0')
const direction = (trip: Trip) => trip.direction === 'outbound' ? `${form.origin} → ${form.destination}` : `${form.destination} → ${form.origin}`
const restAfter = (trips: Trip[], index: number) => { const next = trips[index + 1]; if (!next) return 0; const toMinutes = (time: string) => { const [hour, minute] = time.split(':').map(Number); return hour * 60 + minute }; const gap = toMinutes(next.departure_time) - toMinutes(trips[index].arrival_time); return gap < 0 ? gap + 1_440 : gap }
const cell = (trips: Trip[], index: number) => trips[index] ? { trip: trips[index], rest: restAfter(trips, index) } : null
const minute = (time: string) => { const [hour, minute] = time.split(':').map(Number); return hour * 60 + minute }
const dayStart = computed(() => minute(form.generation!.first_departure))
const dayLength = computed(() => { const end = minute(form.generation!.last_departure); return (end >= dayStart.value ? end : end + 1_440) - dayStart.value + form.generation!.outbound_minutes + form.generation!.inbound_minutes + form.generation!.min_rest_minutes * 2 })
const blockStyle = (time: string, duration: number) => { let start = minute(time); if (start < dayStart.value) start += 1_440; return { left: `${(start - dayStart.value) / dayLength.value * 100}%`, width: `${duration / dayLength.value * 100}%` } }
function generationOrDefault(value: unknown): GenerationSettings { return value && typeof value === 'object' && 'first_departure' in value ? value as GenerationSettings : emptyGeneration() }
async function generate() { if (!canGenerate.value) return; try { error.value = ''; const result = await api.generateSchedule(form); message.value = result.message; if (result.schedule) Object.assign(form, result.schedule) } catch (cause) { error.value = cause instanceof Error ? cause.message : '시간표 생성에 실패했습니다.' } }
async function save() { try { emit('saved', props.schedule ? await api.updateSchedule(props.schedule.id, form) : await api.createSchedule(form)) } catch (cause) { error.value = cause instanceof Error ? cause.message : '저장에 실패했습니다.' } }
async function removeSchedule() { if (props.schedule && confirm('이 시간표를 삭제할까요?')) { await api.deleteSchedule(props.schedule.id); emit('deleted', props.schedule.id) } }
function reset(schedule: Schedule | null) { Object.assign(form, schedule ? { ...schedule, generation: generationOrDefault(schedule.generation), stops: schedule.stops ?? [], trips: schedule.trips.map(({ duration_minutes, required_average_speed_kmh, ...trip }) => trip), activities: schedule.activities.map(({ end_time, total_minutes, ...activity }) => activity) } : emptySchedule()); error.value = ''; message.value = '' }
watch(() => props.schedule, reset, { immediate: true })
</script>

<template>
  <div class="container">
    <header class="app-header"><div><h1>🚌 시내버스 배차 시간표 자동 생성기</h1><p>첫차·막차, 운행시간, 휴식시간, 차량 수에 맞춰 하루 회차표를 만듭니다.</p></div><button v-if="schedule" class="secondary danger" @click="removeSchedule">삭제</button></header>
    <div class="layout"><aside class="sidebar panel"><h2>배차 기본 조건</h2><div class="form-grid"><label>시간표 이름<input v-model.trim="form.name" /></label><label>기점<input v-model.trim="form.origin" /></label><label>종점<input v-model.trim="form.destination" /></label><label>기점 첫차<input v-model="form.generation!.first_departure" type="time" /></label><label>기점 막차<input v-model="form.generation!.last_departure" type="time" /></label><label>기점 → 종점 (분)<input v-model.number="form.generation!.outbound_minutes" type="number" min="1" /></label><label>종점 → 기점 (분)<input v-model.number="form.generation!.inbound_minutes" type="number" min="1" /></label><label>최소 휴식 (분)<input v-model.number="form.generation!.min_rest_minutes" type="number" min="0" /></label><label>인가 차량 대수<input v-model.number="form.generation!.bus_count" type="number" min="1" /></label><label>배차 간격 (분)<input v-model.number="form.generation!.interval_minutes" type="number" min="0" /><small>0이면 자동 계산</small></label></div><button class="primary block" :disabled="!canGenerate" @click="generate">⚡ 배차 스케줄 자동 생성</button><button v-if="form.trips.length" class="secondary block" @click="save">저장</button><p v-if="message" class="success">{{ message }}</p><p v-if="error" class="error">{{ error }}</p><div v-if="form.trips.length" class="stats"><h3>운행 요약</h3><p><span>산출 배차간격</span><b>{{ form.headway_minutes }}분</b></p><p><span>총 운행 횟수</span><b>{{ totalTrips }}회</b></p><p><span>차량당 평균 회차</span><b>{{ averageRounds }}회</b></p></div></aside>
      <section class="content"><div v-if="!form.trips.length" class="panel empty"><b>📅 배차 결과가 없습니다</b><p>왼쪽 조건을 입력하고 자동 생성 버튼을 눌러 주세요.</p></div><section v-else class="panel results"><nav><button :class="{ active: tab === 'matrix' }" @click="tab = 'matrix'">▦ 차량별 회차 시간표</button><button :class="{ active: tab === 'all' }" @click="tab = 'all'">☷ 순서별 전체 운행표</button><button :class="{ active: tab === 'timeline' }" @click="tab = 'timeline'">▤ 운행 타임라인</button></nav><p class="info">💡 차량별 순번과 출발·도착 시간, 다음 운행 전 휴식시간을 한눈에 확인합니다.</p>
        <div v-if="tab === 'matrix'" class="table-wrap"><table class="matrix"><thead><tr><th rowspan="2">차량</th><th v-for="round in rounds" :key="round" colspan="2">{{ round }}회차</th></tr><tr><template v-for="round in rounds" :key="round"><th class="go">기점 → 종점</th><th class="back">종점 → 기점</th></template></tr></thead><tbody><tr v-for="row in vehicleRows" :key="row.bus.id"><th>{{ row.bus.name }}</th><template v-for="index in rounds * 2" :key="index"><td v-if="cell(row.trips, index - 1)"><b>{{ cell(row.trips, index - 1)!.trip.departure_time }} ~ {{ cell(row.trips, index - 1)!.trip.arrival_time }}</b><small>{{ direction(cell(row.trips, index - 1)!.trip) }}</small><em v-if="cell(row.trips, index - 1)!.rest">휴식 {{ cell(row.trips, index - 1)!.rest }}분</em></td><td v-else>-</td></template></tr></tbody></table></div>
        <div v-else-if="tab === 'all'" class="table-wrap"><table><thead><tr><th>차량</th><th>회차</th><th>방향</th><th>출발</th><th>도착</th></tr></thead><tbody><tr v-for="(trip, index) in sortedTrips" :key="trip.id"><td>{{ form.buses.find(bus => bus.id === trip.bus_id)?.name }}</td><td>{{ Math.floor(index / 2) + 1 }}회차</td><td>{{ direction(trip) }}</td><td>{{ trip.departure_time }}</td><td>{{ trip.arrival_time }}</td></tr></tbody></table></div>
        <div v-else class="timeline"><div v-for="row in vehicleRows" :key="row.bus.id" class="timeline-row"><b>{{ row.bus.name }}</b><div class="track"><template v-for="trip in row.trips" :key="trip.id"><span class="trip-block" :class="trip.direction" :style="blockStyle(trip.departure_time, minute(trip.arrival_time) - minute(trip.departure_time))">{{ trip.direction === 'outbound' ? '상행' : '하행' }}</span></template></div></div></div>
      </section></section></div>
  </div>
</template>
