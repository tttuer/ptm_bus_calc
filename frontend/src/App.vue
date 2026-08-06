<template>
  <div class="container animate-fade-in">
    <!-- Header -->
    <header class="app-header">
      <div class="logo-area">
        <span class="bus-icon">🚌</span>
        <div>
          <h1>시내버스 배차 시간표 자동 생성기</h1>
          <p class="subtitle">기점/종점 소요 시간, 휴게시간 조건에 맞춤형 하루 운행 스케줄을 실시간 구축합니다.</p>
        </div>
      </div>
      <div class="header-actions" v-if="scheduleList.length > 0">
        <button class="btn btn-secondary" @click="exportExcel">
          <span class="btn-icon">📥</span> 엑셀 다운로드
        </button>
      </div>
    </header>

    <div class="main-layout">
      <!-- Sidebar Settings -->
      <aside class="sidebar glass-panel">
        <h2 class="section-title">배차 기본 조건 입력</h2>

        <form @submit.prevent="generateSchedule" class="config-form">
          <div class="form-group-row">
            <div class="form-group">
              <label for="first_departure">기점 첫차 출발</label>
              <input
                id="first_departure"
                type="time"
                v-model="config.first_departure"
                required
              />
            </div>
            <div class="form-group">
              <label for="last_departure">기점 막차 출발</label>
              <input
                id="last_departure"
                type="time"
                v-model="config.last_departure"
                required
              />
            </div>
          </div>

          <div class="form-group-row">
            <div class="form-group">
              <label for="one_way_time">기점 ➔ 종점 (분)</label>
              <input
                id="one_way_time"
                type="number"
                v-model.number="config.one_way_time"
                min="5"
                required
              />
            </div>
            <div class="form-group">
              <label for="return_way_time">종점 ➔ 기점 (분)</label>
              <input
                id="return_way_time"
                type="number"
                v-model.number="config.return_way_time"
                min="5"
                required
              />
            </div>
          </div>

          <div class="form-group-row">
            <div class="form-group">
              <label for="min_rest_time">최소 휴게 시간 (분)</label>
              <input
                id="min_rest_time"
                type="number"
                v-model.number="config.min_rest_time"
                min="0"
                required
              />
            </div>
            <div class="form-group">
              <label for="bus_count">인가 차량 대수 (대)</label>
              <input
                id="bus_count"
                type="number"
                v-model.number="config.bus_count"
                min="1"
                required
              />
            </div>
          </div>

          <div class="form-group">
            <label for="interval_minutes">희망 배차 간격 (분) <span class="label-sub">(0 입력 시 자동계산)</span></label>
            <input
              id="interval_minutes"
              type="number"
              v-model.number="config.interval_minutes"
              min="0"
              placeholder="예: 15 (0이면 최적 산출)"
            />
          </div>

          <button type="submit" class="btn btn-primary btn-block" :disabled="loading">
            <span v-if="loading" class="spinner"></span>
            <span v-else>⚡ 배차 스케줄 자동 생성</span>
          </button>
        </form>

        <!-- Stats Panel -->
        <div v-if="scheduleList.length > 0" class="stats-panel">
          <h3 class="stats-title">📊 실시간 운행 요약</h3>
          <div class="stats-grid">
            <div class="stat-card">
              <span class="stat-label">산출 배차 간격</span>
              <span class="stat-val text-accent">{{ calculatedInterval }}분</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">총 운행 횟수</span>
              <span class="stat-val">{{ totalTrips }}회</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">차량당 평균 회차</span>
              <span class="stat-val">{{ avgTripsPerBus }}회</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">일일 막차 도착</span>
              <span class="stat-val text-muted">{{ lastArrivalTime }}</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- Dashboard Results -->
      <main class="dashboard-content">
        <div v-if="error" class="alert alert-error">
          ⚠️ {{ error }}
        </div>

        <!-- Warning Panel for Time Conflicts or Rest Deficits -->
        <div v-if="warnings && warnings.length > 0" class="alert alert-warning animate-fade-in">
          <div class="warning-title">🚨 배차 시간표 세부 검증 알림</div>
          <ul class="warning-list">
            <li v-for="(warn, idx) in warnings" :key="idx">{{ warn }}</li>
          </ul>
        </div>

        <div v-if="scheduleList.length === 0 && !loading" class="empty-state glass-panel">
          <div class="empty-icon">📅</div>
          <h3>배차 결과가 없습니다</h3>
          <p>좌측 입력창에 원하는 배차 조건을 채운 후 버튼을 클릭하여 스케줄을 만들어보세요.</p>
        </div>

        <div v-if="scheduleList.length > 0" class="results-board glass-panel">
          <!-- View Tabs -->
          <div class="tab-header">
            <button
              class="tab-btn"
              :class="{ active: activeTab === 'matrix' }"
              @click="activeTab = 'matrix'"
            >
              📅 차량별 회차 시간표 (추천)
            </button>
            <button
              class="tab-btn"
              :class="{ active: activeTab === 'table' }"
              @click="activeTab = 'table'"
            >
              📋 순서별 전체 일람표 (수동 편집)
            </button>
            <button
              class="tab-btn"
              :class="{ active: activeTab === 'timeline' }"
              @click="activeTab = 'timeline'"
            >
              📊 운행 타임라인 (Gantt)
            </button>
          </div>

          <!-- Tab Content 1: Matrix View (차량별 회차 시간표 - 직관적 시간 중심) -->
          <div v-if="activeTab === 'matrix'" class="tab-content matrix-container">
            <div class="matrix-info">
              <p>💡 각 차량(호차)의 순번별 <strong>[출발시간 ➔ 도착시간]</strong>과 회차 후 <strong>[휴식시간]</strong>이 한눈에 표기됩니다.</p>
            </div>

            <div class="matrix-table-wrapper">
              <table class="matrix-table">
                <thead>
                  <tr>
                    <th class="sticky-col">차량</th>
                    <th v-for="r in maxRoundCount" :key="r" colspan="2" class="round-header">
                      {{ r }}회차
                    </th>
                  </tr>
                  <tr>
                    <th class="sticky-col sub-th">번호</th>
                    <template v-for="r in maxRoundCount" :key="'sub-'+r">
                      <th class="sub-th dir-go">기점 ➔ 종점</th>
                      <th class="sub-th dir-back">종점 ➔ 기점</th>
                    </template>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="busId in uniqueBusIds" :key="busId">
                    <td class="sticky-col bus-cell">
                      <strong>{{ busId }}호차</strong>
                    </td>
                    <template v-for="r in maxRoundCount" :key="busId+'-'+r">
                      <!-- GO direction -->
                      <td class="time-cell go-cell">
                        <div v-if="getTrip(busId, r, 'GO')" class="cell-content">
                          <span class="cell-time">
                            {{ getTrip(busId, r, 'GO').departure_time }} ~ {{ getTrip(busId, r, 'GO').arrival_time }}
                          </span>
                          <span v-if="getTrip(busId, r, 'GO').rest_time_after > 0" class="cell-rest">
                            (휴식 {{ getTrip(busId, r, 'GO').rest_time_after }}분)
                          </span>
                        </div>
                        <span v-else class="text-muted">-</span>
                      </td>

                      <!-- BACK direction -->
                      <td class="time-cell back-cell">
                        <div v-if="getTrip(busId, r, 'BACK')" class="cell-content">
                          <span class="cell-time">
                            {{ getTrip(busId, r, 'BACK').departure_time }} ~ {{ getTrip(busId, r, 'BACK').arrival_time }}
                          </span>
                          <span v-if="getTrip(busId, r, 'BACK').rest_time_after > 0" class="cell-rest">
                            (휴식 {{ getTrip(busId, r, 'BACK').rest_time_after }}분)
                          </span>
                        </div>
                        <span v-else class="text-muted">-</span>
                      </td>
                    </template>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Tab Content 2: Table Grid (수동 편집 일람표) -->
          <div v-if="activeTab === 'table'" class="tab-content table-container">
            <table class="schedule-table">
              <thead>
                <tr>
                  <th>차량</th>
                  <th>회차</th>
                  <th>운행 구분</th>
                  <th>출발 시각</th>
                  <th>도착 시각</th>
                  <th>대기/휴게</th>
                  <th>동작</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(entry, index) in scheduleList" :key="index" :class="{ 'row-back': entry.direction === 'BACK' }">
                  <td><strong>{{ entry.bus_id }}호차</strong></td>
                  <td>{{ entry.round_no }}회차</td>
                  <td>
                    <span :class="['badge', entry.direction === 'GO' ? 'badge-go' : 'badge-back']">
                      {{ entry.direction === 'GO' ? '기점 ➔ 종점' : '종점 ➔ 기점' }}
                    </span>
                  </td>

                  <!-- Departure time cell -->
                  <td>
                    <div v-if="editingIndex === index" class="inline-edit">
                      <input type="time" v-model="editForm.departure_time" class="table-input" />
                    </div>
                    <span v-else class="time-bold">{{ entry.departure_time }}</span>
                  </td>

                  <!-- Arrival time cell -->
                  <td>
                    <div v-if="editingIndex === index" class="inline-edit">
                      <input type="time" v-model="editForm.arrival_time" class="table-input" />
                    </div>
                    <span v-else class="time-bold">{{ entry.arrival_time }}</span>
                  </td>

                  <!-- Rest Time cell -->
                  <td class="text-right">
                    <span v-if="entry.rest_time_after > 0" class="rest-highlight">
                      {{ entry.rest_time_after }}분
                    </span>
                    <span v-else class="text-muted">-</span>
                  </td>

                  <!-- Action Buttons -->
                  <td>
                    <div v-if="editingIndex === index" class="table-actions">
                      <button class="btn-table btn-table-save" @click="saveRow(index)">✔️ 저장</button>
                      <button class="btn-table btn-table-cancel" @click="cancelRow">취소</button>
                    </div>
                    <button v-else class="btn-table btn-table-edit" @click="editRow(index, entry)">
                      ✏️ 수정
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Tab Content 3: Timeline Gantt (확장된 눈금 및 짤림 방지) -->
          <div v-if="activeTab === 'timeline'" class="tab-content timeline-container">
            <div class="timeline-wrapper">
              <div class="timeline-scale">
                <div class="scale-spacer">차량</div>
                <div class="scale-hours">
                  <span v-for="hour in timelineHours" :key="hour" class="scale-hour">
                    {{ String(hour).padStart(2, '0') }}:00
                  </span>
                </div>
              </div>

              <div class="timeline-rows">
                <div v-for="busId in uniqueBusIds" :key="busId" class="timeline-row">
                  <div class="bus-label">{{ busId }}호차</div>
                  <div class="timeline-bar-area">
                    <!-- Hour Grid Lines -->
                    <div class="grid-lines">
                      <div v-for="hour in timelineHours" :key="'grid-'+hour" class="grid-line"></div>
                    </div>

                    <!-- Trip & Rest Blocks -->
                    <template v-for="(entry, index) in getBusSchedule(busId)" :key="index">
                      <!-- Operation Block -->
                      <div
                        class="time-block operation-block"
                        :style="getBlockStyle(entry.departure_time, entry.arrival_time)"
                        :title="`${entry.bus_id}호차 ${entry.round_no}회차 [${entry.direction === 'GO' ? '기점➔종점' : '종점➔기점'}]\n출발: ${entry.departure_time} | 도착: ${entry.arrival_time}`"
                      >
                        <span class="block-text">
                          {{ entry.departure_time }}~{{ entry.arrival_time }}
                        </span>
                      </div>

                      <!-- Rest Block -->
                      <div
                        v-if="entry.rest_time_after > 0"
                        class="time-block rest-block"
                        :style="getRestBlockStyle(entry.arrival_time, entry.rest_time_after)"
                        :title="`대기 및 휴식: ${entry.rest_time_after}분`"
                      >
                        <span class="block-text rest-text">휴식 {{ entry.rest_time_after }}분</span>
                      </div>
                    </template>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'

const API_BASE = 'http://localhost:8001/api'

// Config form data
const config = reactive({
  first_departure: '06:00',
  last_departure: '22:30',
  one_way_time: 60,
  return_way_time: 60,
  min_rest_time: 15,
  bus_count: 5,
  interval_minutes: 15
})

const loading = ref(false)
const error = ref('')
const warnings = ref([])
const activeTab = ref('matrix') // Default: Matrix View
const calculatedInterval = ref(0)
const scheduleList = ref([])

// Editing row index
const editingIndex = ref(-1)
const editForm = reactive({
  departure_time: '',
  arrival_time: ''
})

// Time parsing helpers
const timeToMin = (t) => {
  if (!t) return 0
  const [h, m] = t.split(':').map(Number)
  return h * 60 + m
}

const minToTime = (min) => {
  const h = Math.floor(min / 60) % 24
  const m = min % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
}

// Compute Max Round Count across all buses
const maxRoundCount = computed(() => {
  if (scheduleList.value.length === 0) return 0
  const rounds = scheduleList.value.map(e => e.round_no)
  return Math.max(...rounds)
})

// Helper for Matrix View cell retrieval
const getTrip = (busId, roundNo, direction) => {
  return scheduleList.value.find(
    e => e.bus_id === busId && e.round_no === roundNo && e.direction === direction
  )
}

// Timeline time boundaries
const timelineMinTime = computed(() => {
  if (scheduleList.value.length === 0) return 360 // 06:00
  const times = scheduleList.value.map(e => timeToMin(e.departure_time))
  return Math.min(...times) - 20
})

const timelineMaxTime = computed(() => {
  if (scheduleList.value.length === 0) return 1440 // 24:00
  const times = scheduleList.value.map(e => {
    const arr = timeToMin(e.arrival_time)
    return arr + (e.rest_time_after || 0)
  })
  return Math.max(...times) + 20
})

const timelineHours = computed(() => {
  const startHour = Math.floor(timelineMinTime.value / 60)
  const endHour = Math.ceil(timelineMaxTime.value / 60)
  const hours = []
  for (let h = startHour; h <= endHour; h++) {
    hours.push(h)
  }
  return hours
})

// Stats Computations
const totalTrips = computed(() => scheduleList.value.length)
const uniqueBusIds = computed(() => {
  const ids = scheduleList.value.map(e => e.bus_id)
  return [...new Set(ids)].sort((a, b) => a - b)
})

const avgTripsPerBus = computed(() => {
  if (uniqueBusIds.value.length === 0) return 0
  return (totalTrips.value / uniqueBusIds.value.length).toFixed(1)
})

const lastArrivalTime = computed(() => {
  if (scheduleList.value.length === 0) return '-'
  const arrivals = scheduleList.value.map(e => timeToMin(e.arrival_time))
  return minToTime(Math.max(...arrivals))
})

// Timeline Styles Builder
const getBlockStyle = (depStr, arrStr) => {
  const dep = timeToMin(depStr)
  const arr = timeToMin(arrStr)

  const totalDuration = timelineMaxTime.value - timelineMinTime.value
  const left = ((dep - timelineMinTime.value) / totalDuration) * 100
  const width = ((arr - dep) / totalDuration) * 100

  return {
    left: `${left}%`,
    width: `${width}%`
  }
}

const getRestBlockStyle = (arrStr, restMin) => {
  const arr = timeToMin(arrStr)
  const totalDuration = timelineMaxTime.value - timelineMinTime.value
  const left = ((arr - timelineMinTime.value) / totalDuration) * 100
  const width = (restMin / totalDuration) * 100

  return {
    left: `${left}%`,
    width: `${width}%`
  }
}

const getBusSchedule = (busId) => {
  return scheduleList.value.filter(e => e.bus_id === busId)
}

// Fetch Schedule
const generateSchedule = async () => {
  loading.value = true
  error.value = ''
  warnings.value = []
  try {
    const res = await fetch(`${API_BASE}/schedule/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    })

    if (!res.ok) {
      const errData = await res.json()
      throw new Error(errData.detail || '배차 생성 실패')
    }

    const data = await res.json()
    scheduleList.value = data.schedule
    calculatedInterval.value = data.interval_minutes
    warnings.value = data.warnings || []
  } catch (err) {
    error.value = err.message
    scheduleList.value = []
    warnings.value = []
  } finally {
    loading.value = false
  }
}

// Edit Row actions
const editRow = (index, entry) => {
  editingIndex.value = index
  editForm.departure_time = entry.departure_time
  editForm.arrival_time = entry.arrival_time
}

const cancelRow = () => {
  editingIndex.value = -1
}

const saveRow = (index) => {
  const row = scheduleList.value[index]
  row.departure_time = editForm.departure_time
  row.arrival_time = editForm.arrival_time

  recalculateRestTimes(row.bus_id)
  editingIndex.value = -1
}

const recalculateRestTimes = (busId) => {
  const busEntries = scheduleList.value.filter(e => e.bus_id === busId)
  busEntries.sort((a, b) => timeToMin(a.departure_time) - timeToMin(b.departure_time))

  for (let i = 0; i < busEntries.length; i++) {
    const curr = busEntries[i]
    const next = busEntries[i + 1]

    if (next) {
      const currArr = timeToMin(curr.arrival_time)
      let nextDep = timeToMin(next.departure_time)
      if (nextDep < currArr) {
        nextDep += 1440
      }
      curr.rest_time_after = nextDep - currArr
    } else {
      curr.rest_time_after = 0
    }
  }
}

// Export excel
const exportExcel = async () => {
  try {
    const res = await fetch(`${API_BASE}/schedule/export-excel`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(scheduleList.value)
    })

    if (!res.ok) throw new Error('엑셀 추출에 실패하였습니다.')

    const blob = await res.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `시내버스_배차시간표_${new Date().toISOString().slice(0,10)}.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (err) {
    alert(err.message)
  }
}
</script>

<style scoped>
.container {
  max-width: 1500px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
  box-sizing: border-box;
}

/* Header styling */
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  border-bottom: 1px solid var(--panel-border);
  padding-bottom: 1.5rem;
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.bus-icon {
  font-size: 2.8rem;
  filter: drop-shadow(0 0 10px var(--primary-glow));
}

.app-header h1 {
  font-size: 2rem;
  font-weight: 800;
  margin: 0;
  background: linear-gradient(to right, #60a5fa, #3b82f6, #f59e0b);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  color: var(--text-muted);
  margin: 0.25rem 0 0 0;
  font-size: 0.95rem;
}

/* Main Layout Grid */
.main-layout {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 2rem;
  align-items: start;
}

/* Sidebar Styling & Input Overflow Fix */
.sidebar {
  padding: 1.5rem;
  box-sizing: border-box;
  width: 100%;
}

.section-title {
  font-size: 1.2rem;
  font-weight: 700;
  margin-top: 0;
  margin-bottom: 1.25rem;
  border-left: 4px solid var(--primary);
  padding-left: 0.75rem;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
  width: 100%;
  box-sizing: border-box;
}

.form-group-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
  width: 100%;
  box-sizing: border-box;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.form-group label {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.label-sub {
  font-size: 0.72rem;
  font-weight: 400;
  color: var(--accent);
}

.form-group input {
  width: 100%;
  box-sizing: border-box;
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid var(--panel-border);
  border-radius: 8px;
  color: #fff;
  padding: 0.65rem 0.5rem;
  font-family: inherit;
  font-size: 0.9rem;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-weight: 700;
  font-size: 0.95rem;
  border-radius: 8px;
  padding: 0.85rem 1.5rem;
  border: none;
}

.btn-primary {
  background: var(--primary);
  color: #fff;
  box-shadow: 0 4px 14px var(--primary-glow);
}

.btn-primary:hover {
  background: var(--primary-hover);
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.5);
}

.btn-secondary {
  background: rgba(245, 158, 11, 0.15);
  color: var(--accent);
  border: 1px solid rgba(245, 158, 11, 0.4);
}

.btn-secondary:hover {
  background: rgba(245, 158, 11, 0.25);
  color: #fff;
  border-color: var(--accent);
}

.btn-block {
  width: 100%;
}

/* Stats Panel */
.stats-panel {
  margin-top: 1.5rem;
  border-top: 1px solid var(--panel-border);
  padding-top: 1.25rem;
}

.stats-title {
  font-size: 1rem;
  font-weight: 700;
  margin-top: 0;
  margin-bottom: 0.85rem;
  color: var(--text-muted);
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.65rem;
}

.stat-card {
  background: rgba(15, 23, 42, 0.4);
  border: 1px solid var(--panel-border);
  border-radius: 8px;
  padding: 0.65rem;
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-bottom: 0.2rem;
}

.stat-val {
  font-size: 1.1rem;
  font-weight: 800;
}

.text-accent {
  color: var(--accent);
}

/* Dashboard Content */
.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  min-width: 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 5rem 2rem;
  text-align: center;
}

.empty-icon {
  font-size: 3.5rem;
  margin-bottom: 1rem;
  opacity: 0.6;
}

.alert {
  padding: 1rem;
  border-radius: 8px;
  font-weight: 600;
}

.alert-error {
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: var(--danger);
}

.alert-warning {
  background: rgba(245, 158, 11, 0.12);
  border: 1px solid rgba(245, 158, 11, 0.35);
  color: #fbbf24;
}

.warning-title {
  font-weight: 800;
  font-size: 0.95rem;
  margin-bottom: 0.4rem;
}

.warning-list {
  margin: 0;
  padding-left: 1.25rem;
  font-size: 0.85rem;
}

.warning-list li {
  margin-bottom: 0.2rem;
}

/* Results Board Tabs */
.results-board {
  padding: 1.5rem;
  overflow: hidden;
  box-sizing: border-box;
}

.tab-header {
  display: flex;
  gap: 0.75rem;
  border-bottom: 1px solid var(--panel-border);
  margin-bottom: 1.25rem;
  padding-bottom: 0.5rem;
  overflow-x: auto;
}

.tab-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 0.95rem;
  font-weight: 700;
  padding: 0.6rem 1rem;
  position: relative;
  white-space: nowrap;
}

.tab-btn:hover {
  color: #fff;
}

.tab-btn.active {
  color: var(--primary);
}

.tab-btn.active::after {
  content: '';
  position: absolute;
  bottom: -0.55rem;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--primary);
  border-radius: 3px;
}

/* Matrix Table View (시간 중심 매트릭스 시간표) */
.matrix-info {
  margin-bottom: 1rem;
  font-size: 0.88rem;
  color: var(--text-muted);
  background: rgba(59, 130, 246, 0.08);
  border: 1px solid rgba(59, 130, 246, 0.2);
  padding: 0.75rem 1rem;
  border-radius: 8px;
}

.matrix-table-wrapper {
  overflow-x: auto;
  max-width: 100%;
  border: 1px solid var(--panel-border);
  border-radius: 8px;
}

.matrix-table {
  width: 100%;
  border-collapse: collapse;
  text-align: center;
  font-size: 0.85rem;
}

.matrix-table th,
.matrix-table td {
  padding: 0.75rem 0.6rem;
  border: 1px solid var(--panel-border);
  white-space: nowrap;
}

.matrix-table th {
  background: rgba(15, 23, 42, 0.8);
  font-weight: 700;
}

.round-header {
  background: rgba(30, 41, 59, 0.9) !important;
  color: var(--accent);
  font-size: 0.9rem;
}

.sub-th {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.dir-go {
  color: #60a5fa;
}

.dir-back {
  color: #34d399;
}

.sticky-col {
  position: sticky;
  left: 0;
  background: #0f172a !important;
  z-index: 5;
  font-weight: 800;
  width: 70px;
}

.bus-cell {
  color: #fff;
  font-size: 0.95rem;
}

.time-cell {
  background: rgba(15, 23, 42, 0.2);
}

.cell-content {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.cell-time {
  font-weight: 700;
  font-size: 0.88rem;
  color: #f8fafc;
}

.cell-rest {
  font-size: 0.72rem;
  color: var(--accent);
}

/* Schedule Table */
.table-container {
  overflow-x: auto;
}

.schedule-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.schedule-table th,
.schedule-table td {
  padding: 0.75rem 0.85rem;
  border-bottom: 1px solid var(--panel-border);
}

.schedule-table th {
  font-weight: 700;
  color: var(--text-muted);
  font-size: 0.85rem;
}

.time-bold {
  font-weight: 700;
  font-size: 0.95rem;
  color: #fff;
}

.row-back {
  background: rgba(255, 255, 255, 0.015);
}

.badge {
  display: inline-block;
  padding: 0.2rem 0.45rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
}

.badge-go {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.badge-back {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.rest-highlight {
  color: var(--accent);
  font-weight: 700;
}

.text-right {
  text-align: right;
}

/* Inline Editing */
.inline-edit {
  display: flex;
}

.table-input {
  background: #1e293b;
  border: 1px solid var(--primary);
  border-radius: 4px;
  color: #fff;
  padding: 0.25rem 0.4rem;
  font-family: inherit;
  font-size: 0.85rem;
}

.table-actions {
  display: flex;
  gap: 0.4rem;
}

.btn-table {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--panel-border);
  color: #fff;
  border-radius: 4px;
  padding: 0.3rem 0.5rem;
  font-size: 0.78rem;
}

.btn-table:hover {
  background: rgba(255, 255, 255, 0.15);
}

.btn-table-save {
  background: rgba(16, 185, 129, 0.2);
  border-color: var(--success);
  color: var(--success);
}

.btn-table-cancel {
  background: rgba(239, 68, 68, 0.2);
  border-color: var(--danger);
  color: var(--danger);
}

.btn-table-edit {
  border-color: rgba(255, 255, 255, 0.15);
}

.btn-table-edit:hover {
  border-color: var(--primary);
  color: var(--primary);
}

/* Gantt Chart Timeline View */
.timeline-container {
  overflow-x: auto;
}

.timeline-wrapper {
  min-width: 1000px;
}

.timeline-scale {
  display: flex;
  margin-bottom: 0.75rem;
  position: relative;
}

.scale-spacer {
  width: 80px;
  flex-shrink: 0;
  font-weight: 700;
  font-size: 0.8rem;
  color: var(--text-muted);
}

.scale-hours {
  display: flex;
  justify-content: space-between;
  width: 100%;
  position: relative;
}

.scale-hour {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-weight: 600;
  transform: translateX(-50%);
}

.timeline-rows {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.timeline-row {
  display: flex;
  align-items: center;
}

.bus-label {
  width: 80px;
  flex-shrink: 0;
  font-weight: 800;
  font-size: 0.9rem;
  color: var(--text-muted);
}

.timeline-bar-area {
  position: relative;
  width: 100%;
  height: 44px;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid var(--panel-border);
  border-radius: 8px;
  overflow: hidden;
}

.grid-lines {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: space-between;
  pointer-events: none;
}

.grid-line {
  width: 1px;
  height: 100%;
  background: rgba(255, 255, 255, 0.05);
}

/* Blocks */
.time-block {
  position: absolute;
  top: 5px;
  height: 34px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  overflow: hidden;
  white-space: nowrap;
  box-sizing: border-box;
  padding: 0 4px;
}

.operation-block {
  background: linear-gradient(90deg, #2563eb, #3b82f6);
  border: 1px solid rgba(59, 130, 246, 0.6);
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
  color: #fff;
}

.operation-block:hover {
  transform: scaleY(1.08);
  filter: brightness(1.2);
  z-index: 10;
}

.rest-block {
  background: rgba(245, 158, 11, 0.18);
  border: 1px dashed rgba(245, 158, 11, 0.6);
  color: var(--accent);
}

.rest-block:hover {
  background: rgba(245, 158, 11, 0.3);
}

.block-text {
  font-size: 0.75rem;
  font-weight: 700;
}

.rest-text {
  font-style: italic;
  font-size: 0.7rem;
}

.spinner {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  border: 2px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 1024px) {
  .main-layout {
    grid-template-columns: 1fr;
  }
}
</style>
