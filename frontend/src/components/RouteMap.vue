<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { loadKakaoMap } from '../map'
import type { Stop } from '../types'

const props = defineProps<{ stops: Stop[]; selectedIndex: number }>()
const emit = defineEmits<{ coordinate: [number, number]; place: [string, number, number] }>()
const element = ref<HTMLElement>()
const ready = ref(false)
const query = ref('')
const results = ref<any[]>([])
const searchMessage = ref('')
let map: any
let kakao: any
let places: any
let overlays: any[] = []

function draw() {
  if (!map) return
  overlays.forEach(item => item.setMap(null))
  const points = props.stops.filter(stop => stop.latitude !== null && stop.longitude !== null)
    .map(stop => new kakao.maps.LatLng(stop.latitude, stop.longitude))
  overlays = points.map((point, index) => new kakao.maps.Marker({ map, position: point, title: `${index + 1}번 정류장` }))
  if (points.length > 1) overlays.push(new kakao.maps.Polyline({ map, path: points, strokeWeight: 4, strokeColor: '#2563eb' }))
  if (points.length) map.setCenter(points[points.length - 1])
}

function search() {
  const keyword = query.value.trim()
  if (!keyword || !places) return
  places.keywordSearch(keyword, (data: any[], status: string) => {
    results.value = status === kakao.maps.services.Status.OK ? data.slice(0, 5) : []
    searchMessage.value = results.value.length ? '' : '검색 결과가 없습니다.'
  })
}

function selectPlace(place: any) {
  const latitude = Number(place.y)
  const longitude = Number(place.x)
  map.panTo(new kakao.maps.LatLng(latitude, longitude))
  results.value = []
  query.value = place.place_name
  emit('place', place.place_name, latitude, longitude)
}

onMounted(async () => {
  kakao = await loadKakaoMap()
  if (!kakao || !element.value) return
  map = new kakao.maps.Map(element.value, { center: new kakao.maps.LatLng(37.5665, 126.978), level: 7 })
  places = new kakao.maps.services.Places(map)
  kakao.maps.event.addListener(map, 'click', (event: any) => emit('coordinate', event.latLng.getLat(), event.latLng.getLng()))
  ready.value = true
  draw()
})

watch(() => [props.stops, props.selectedIndex], draw, { deep: true })
</script>

<template>
  <div class="map-shell">
    <form v-if="ready" class="place-search" @submit.prevent="search">
      <input v-model="query" placeholder="정류장 또는 장소 검색" /><button>검색</button>
    </form>
    <ul v-if="results.length" class="place-results"><li v-for="place in results" :key="place.id" @click="selectPlace(place)"><b>{{ place.place_name }}</b><small>{{ place.road_address_name || place.address_name }}</small></li></ul>
    <div ref="element" class="map"></div>
    <p v-if="!ready" class="map-message">카카오 지도 키를 설정하면 지도가 표시됩니다.</p>
    <p v-else-if="searchMessage" class="search-message">{{ searchMessage }}</p>
  </div>
</template>
