<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { api } from '../api'
import type { Activity, Bus, Driver, Schedule, ScheduleInput, Trip } from '../types'

const props = defineProps<{ schedule: Schedule | null }>()
const emit = defineEmits<{ saved: [Schedule]; deleted: [string] }>()
const form = reactive<ScheduleInput>(emptySchedule())
const error = ref('')
const id = () => crypto.randomUUID()
const canSave = computed(() => form.name && form.origin && form.destination)
const options = <T extends { id: string }>(items: T[]) => items
const emptyBus = (): Bus => ({ id: id(), name: `버스 ${form.buses.length + 1}` })
const emptyDriver = (): Driver => ({ id: id(), name: `기사 ${form.drivers.length + 1}`, work_start: '06:00', work_end: '22:00' })
const emptyTrip = (): Trip => ({ id: id(), direction: 'outbound', departure_time: '09:00', arrival_time: '10:00', distance_km: 1, bus_id: form.buses[0]?.id ?? '', driver_id: form.drivers[0]?.id ?? '' })
const emptyActivity = (): Activity => ({ id: id(), kind: 'rest', start_time: '10:00', bus_id: form.buses[0]?.id ?? '', driver_id: form.drivers[0]?.id ?? null, duration_minutes: 30, to_charger_minutes: 0, to_charger_distance_km: 0, charge_minutes: 30, to_departure_minutes: 0, to_departure_distance_km: 0 })
function emptySchedule(): ScheduleInput { return { name: '', origin: '', destination: '', max_average_speed_kmh: 60, headway_minutes: 30, buses: [], drivers: [], trips: [], activities: [] } }
const shift = (time: string, minutes: number) => { const [hour, minute] = time.split(':').map(Number); const value = (hour * 60 + minute + minutes) % 1_440; return `${String(Math.floor(value / 60)).padStart(2, '0')}:${String(value % 60).padStart(2, '0')}` }
function addTrip() { const last = form.trips[form.trips.length - 1]; form.trips.push(last ? { ...last, id: id(), departure_time: shift(last.departure_time, form.headway_minutes), arrival_time: shift(last.arrival_time, form.headway_minutes) } : emptyTrip()) }
function reset(schedule: Schedule | null) { Object.assign(form, schedule ? { name: schedule.name, origin: schedule.origin, destination: schedule.destination, max_average_speed_kmh: schedule.max_average_speed_kmh, headway_minutes: schedule.headway_minutes, buses: schedule.buses, drivers: schedule.drivers, trips: schedule.trips.map(({ duration_minutes, required_average_speed_kmh, ...trip }) => trip), activities: schedule.activities.map(({ end_time, total_minutes, ...activity }) => activity) } : emptySchedule()); error.value = '' }
function remove<T>(items: T[], index: number) { items.splice(index, 1) }
async function save() { if (!canSave.value) return; try { emit('saved', props.schedule ? await api.updateSchedule(props.schedule.id, form) : await api.createSchedule(form)) } catch (cause) { error.value = cause instanceof Error ? cause.message : '저장에 실패했습니다.' } }
async function removeSchedule() { if (props.schedule && confirm(`'${props.schedule.name}' 시간표를 삭제할까요?`)) { await api.deleteSchedule(props.schedule.id); emit('deleted', props.schedule.id) } }
const tripResult = (trip: Trip) => props.schedule?.trips.find(item => item.id === trip.id)
const activityResult = (activity: Activity) => props.schedule?.activities.find(item => item.id === activity.id)
watch(() => props.schedule, reset, { immediate: true })
</script>

<template>
  <section class="editor">
    <header><h2>{{ schedule ? '시간표 편집' : '새 시간표' }}</h2><button v-if="schedule" class="danger" @click="removeSchedule">삭제</button></header>
    <div class="grid basics"><label>시간표 이름<input v-model.trim="form.name" placeholder="예: 01번 평일" /></label><label>출발지<input v-model.trim="form.origin" placeholder="예: 차고지" /></label><label>도착지<input v-model.trim="form.destination" placeholder="예: 시청" /></label><label>최대 평균속도 (km/h)<input v-model.number="form.max_average_speed_kmh" type="number" min="1" max="120" /></label><label>다음 배차 간격(분)<input v-model.number="form.headway_minutes" type="number" min="1" max="360" /></label></div>

    <section><header><h3>버스와 기사</h3><span><button @click="form.buses.push(emptyBus())">+ 버스</button><button @click="form.drivers.push(emptyDriver())">+ 기사</button></span></header><div class="grid resources"><label v-for="(bus, index) in form.buses" :key="bus.id">버스<input v-model.trim="bus.name" /><button class="danger small" @click="remove(form.buses, index)">삭제</button></label><label v-for="(driver, index) in form.drivers" :key="driver.id">기사<input v-model.trim="driver.name" /><span class="times"><input v-model="driver.work_start" type="time" /><input v-model="driver.work_end" type="time" /></span><button class="danger small" @click="remove(form.drivers, index)">삭제</button></label></div></section>

    <section><header><h3>운행편</h3><button :disabled="!form.buses.length || !form.drivers.length" @click="addTrip">+ 다음 출발시간 추가</button></header><p v-if="!form.trips.length" class="hint">버스와 기사를 추가한 뒤, 출발편을 넣어 주세요.</p><article v-for="(trip, index) in form.trips" :key="trip.id" class="row trip"><select v-model="trip.direction"><option value="outbound">{{ form.origin }} → {{ form.destination }}</option><option value="inbound">{{ form.destination }} → {{ form.origin }}</option></select><input v-model="trip.departure_time" type="time" title="출발" /><input v-model="trip.arrival_time" type="time" title="도착" /><input v-model.number="trip.distance_km" type="number" min="0.1" step="0.1" title="거리(km)" /><select v-model="trip.bus_id"><option v-for="bus in options(form.buses)" :key="bus.id" :value="bus.id">{{ bus.name }}</option></select><select v-model="trip.driver_id"><option v-for="driver in options(form.drivers)" :key="driver.id" :value="driver.id">{{ driver.name }}</option></select><strong v-if="tripResult(trip)">{{ tripResult(trip)?.required_average_speed_kmh }}km/h</strong><span v-else>저장 후 계산</span><button class="danger" @click="remove(form.trips, index)">×</button></article></section>

    <section><header><h3>휴게 · 충전</h3><button :disabled="!form.buses.length" @click="form.activities.push(emptyActivity())">+ 일정 추가</button></header><article v-for="(activity, index) in form.activities" :key="activity.id" class="row activity"><select v-model="activity.kind"><option value="rest">기사 휴게</option><option value="charge">충전</option></select><input v-model="activity.start_time" type="time" /><select v-model="activity.bus_id"><option v-for="bus in options(form.buses)" :key="bus.id" :value="bus.id">{{ bus.name }}</option></select><select v-model="activity.driver_id"><option :value="null">기사 없음</option><option v-for="driver in options(form.drivers)" :key="driver.id" :value="driver.id">{{ driver.name }}</option></select><template v-if="activity.kind === 'rest'"><input v-model.number="activity.duration_minutes" type="number" min="1" placeholder="휴게(분)" /></template><template v-else><input v-model.number="activity.to_charger_minutes" type="number" min="0" placeholder="충전소 이동(분)" /><input v-model.number="activity.to_charger_distance_km" type="number" min="0" step="0.1" placeholder="충전소 거리(km)" /><input v-model.number="activity.charge_minutes" type="number" min="1" placeholder="충전(분)" /><input v-model.number="activity.to_departure_minutes" type="number" min="0" placeholder="출발지 이동(분)" /><input v-model.number="activity.to_departure_distance_km" type="number" min="0" step="0.1" placeholder="출발지 거리(km)" /></template><span v-if="activityResult(activity)">종료 {{ activityResult(activity)?.end_time }}</span><button class="danger" @click="remove(form.activities, index)">×</button></article></section>

    <section v-if="schedule?.issues.length" class="issues"><h3>확인할 점</h3><p v-for="issue in schedule.issues" :key="`${issue.entity_id}-${issue.message}`" :class="issue.severity">{{ issue.severity === 'error' ? '오류' : '주의' }}: {{ issue.message }}</p></section>
    <p v-if="error" class="error">{{ error }}</p><button class="save" :disabled="!canSave" @click="save">저장하고 시간표 검사</button>
  </section>
</template>
