<script setup lang="ts">
import { onMounted, ref } from 'vue'
import RouteEditor from './components/RouteEditor.vue'
import { useRoutesStore } from './stores/routes'
import type { Route } from './types'

const store = useRoutesStore()
const selected = ref<Route | null>(null)

function saved(route: Route) { const index = store.routes.findIndex(item => item.id === route.id); index < 0 ? store.routes.unshift(route) : store.routes.splice(index, 1, route); selected.value = route }
function deleted(id: string) { store.routes = store.routes.filter(route => route.id !== id); selected.value = null }
onMounted(store.load)
</script>

<template>
  <main><aside><h1>버스 시간 계산기</h1><button class="new" @click="selected = null">+ 노선 추가</button><p v-if="store.loading">불러오는 중...</p><button v-for="route in store.routes" :key="route.id" class="route" :class="{ active: route.id === selected?.id }" @click="selected = route"><b>{{ route.name }}</b><small>{{ route.stops.length }}개 정류장 · {{ Math.floor(route.total_seconds / 60) }}분</small></button></aside><RouteEditor :route="selected" @saved="saved" @deleted="deleted" /></main>
</template>
