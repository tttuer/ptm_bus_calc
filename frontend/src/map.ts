declare global {
  interface Window { kakao?: any }
}

let loading: Promise<any> | undefined

export function loadKakaoMap() {
  const key = import.meta.env.VITE_KAKAO_MAP_KEY
  if (!key) return Promise.resolve(undefined)
  if (window.kakao) return Promise.resolve(window.kakao)
  if (!loading) loading = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${key}&autoload=false&libraries=services`
    script.onload = () => window.kakao.maps.load(() => resolve(window.kakao))
    script.onerror = () => reject(new Error('카카오 지도를 불러올 수 없습니다.'))
    document.head.append(script)
  })
  return loading
}
