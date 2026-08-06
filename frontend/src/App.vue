<script setup lang="ts">
import { onMounted, ref } from 'vue'
import ScheduleEditor from './components/ScheduleEditor.vue'
import { useSchedulesStore } from './stores/routes'
import type { Schedule } from './types'

const store = useSchedulesStore()
const selected = ref<Schedule | null>(null)
function saved(schedule: Schedule) { const index = store.schedules.findIndex(item => item.id === schedule.id); index < 0 ? store.schedules.unshift(schedule) : store.schedules.splice(index, 1, schedule); selected.value = schedule }
function deleted(id: string) { store.schedules = store.schedules.filter(schedule => schedule.id !== id); selected.value = null }
onMounted(store.load)
</script>

<template>
  <main><aside><h1>버스 시간표</h1><button class="new" @click="selected = null">+ 시간표 추가</button><p v-if="store.loading">불러오는 중...</p><button v-for="schedule in store.schedules" :key="schedule.id" class="route" :class="{ active: schedule.id === selected?.id }" @click="selected = schedule"><b>{{ schedule.name }}</b><small>{{ schedule.trips.length }}개 운행편 · {{ schedule.issues.length }}개 알림</small></button></aside><ScheduleEditor :schedule="selected" @saved="saved" @deleted="deleted" /></main>
</template>
