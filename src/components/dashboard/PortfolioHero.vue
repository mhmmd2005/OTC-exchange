<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

const canvasRef = ref(null)
let rafId = null

function drawTerrain() {
  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const ratio = window.devicePixelRatio || 1
  const rect = canvas.getBoundingClientRect()
  const width = rect.width
  const height = rect.height

  canvas.width = Math.max(1, width * ratio)
  canvas.height = Math.max(1, height * ratio)
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0)

  const t = performance.now() * 0.0005

  ctx.clearRect(0, 0, width, height)

  const gradient = ctx.createRadialGradient(width * 0.7, height * 0.2, 10, width * 0.7, height * 0.2, width * 0.8)
  gradient.addColorStop(0, 'rgba(241, 208, 137, 0.18)')
  gradient.addColorStop(0.3, 'rgba(212, 169, 90, 0.08)')
  gradient.addColorStop(1, 'rgba(0,0,0,0)')
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, width, height)

  ctx.lineWidth = 1
  ctx.strokeStyle = 'rgba(212,169,90,0.18)'
  for (let y = 0; y < height; y += 24) {
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(width, y)
    ctx.stroke()
  }

  const layers = [
    { amp: 18, color: 'rgba(138,106,47,0.65)', offset: 0.15 },
    { amp: 24, color: 'rgba(212,169,90,0.8)', offset: 0.4 },
    { amp: 30, color: 'rgba(241,208,137,0.9)', offset: 0.7 },
  ]

  layers.forEach((layer, idx) => {
    ctx.beginPath()
    ctx.moveTo(0, height)
    for (let x = 0; x <= width; x += 22) {
      const y = height - (idx === 0 ? 52 : idx === 1 ? 80 : 110) + Math.sin((x + t * 180 + layer.offset * 300) / 80) * layer.amp + Math.cos((x + t * 120) / 42) * 14
      ctx.lineTo(x, y)
    }
    ctx.lineTo(width, height)
    ctx.closePath()
    ctx.fillStyle = idx === 2 ? 'rgba(212,169,90,0.1)' : 'rgba(12,18,30,0.08)'
    ctx.fill()
    ctx.strokeStyle = layer.color
    ctx.stroke()
  })

  ctx.beginPath()
  ctx.moveTo(0, height * 0.75)
  for (let x = 0; x <= width; x += 18) {
    const y = height * 0.75 + Math.sin(x / 36 + t * 1.8) * 10 + Math.cos(x / 80 - t * 2.2) * 6
    ctx.lineTo(x, y)
  }
  ctx.lineTo(width, height)
  ctx.lineTo(0, height)
  ctx.closePath()
  ctx.fillStyle = 'rgba(212,169,90,0.08)'
  ctx.fill()

  ctx.beginPath()
  ctx.moveTo(0, height * 0.62)
  for (let x = 0; x <= width; x += 14) {
    const y = height * 0.62 + Math.sin((x + t * 200) / 42) * 12
    ctx.lineTo(x, y)
  }
  ctx.strokeStyle = 'rgba(241,208,137,0.85)'
  ctx.shadowBlur = 12
  ctx.shadowColor = 'rgba(241,208,137,0.6)'
  ctx.stroke()
  ctx.shadowBlur = 0

  ctx.beginPath()
  for (let i = 0; i < 90; i++) {
    const x = Math.random() * width
    const y = Math.random() * height * 0.75
    const r = Math.random() * 1.8 + 0.4
    ctx.moveTo(x, y)
    ctx.arc(x, y, r, 0, Math.PI * 2)
  }
  ctx.fillStyle = 'rgba(241,208,137,0.28)'
  ctx.fill()
}

function animate() {
  drawTerrain()
  rafId = requestAnimationFrame(animate)
}

onMounted(() => {
  animate()
  window.addEventListener('resize', drawTerrain)
})

onBeforeUnmount(() => {
  if (rafId) cancelAnimationFrame(rafId)
  window.removeEventListener('resize', drawTerrain)
})
</script>

<template>
  <section class="portfolio-hero panel-surface">
    <div class="hero-topline">
      <div class="market-status-pill">
        <span class="pulse-dot" />
        وضعیت بازار
      </div>
      <div class="hero-badge">باز</div>
    </div>

    <div class="hero-main-copy">
      <span class="field-label">ارزش کل دارایی‌ها</span>
      <div class="hero-balance">۲٬۱۲۸٬۴۳۰٬۰۰۰</div>
      <div class="hero-trend-row">
        <span class="trend-pill positive">+۲.۴۸٪</span>
        <span class="trend-copy">(+۵۱٬۴۳۰٬۰۰۰)</span>
      </div>
    </div>

    <div class="hero-canvas-wrap">
      <canvas ref="canvasRef" />
    </div>

    <div class="hero-metrics">
      <div class="metric-box">
        <span>موجودی قفل شده</span>
        <strong>۴۵۰٬۰۰۰٬۰۰۰</strong>
      </div>
      <div class="metric-box">
        <span>ارزش در دسترس</span>
        <strong>۱٬۶۸۰٬۰۰۰٬۰۰۰</strong>
      </div>
      <div class="metric-box">
        <span>بیشترین دارایی</span>
        <strong>BTC</strong>
      </div>
      <div class="metric-box">
        <span>سود و زیان ۲۴ ساعته</span>
        <strong class="positive">+۴۶٬۲۵۰٬۰۰۰</strong>
      </div>
    </div>
  </section>
</template>

<style scoped>
.portfolio-hero {
  position: relative;
  overflow: hidden;
  min-height: 420px;
  padding: 22px 22px 18px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  background: linear-gradient(180deg, rgba(11,17,28,0.9), rgba(12,18,30,0.82));
}

.hero-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  position: relative;
  z-index: 2;
}

.market-status-pill,
.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.68rem;
  font-weight: 700;
  border-radius: 999px;
  padding: 7px 10px;
}

.market-status-pill {
  background: rgba(22, 199, 132, 0.08);
  color: #88f0c0;
  border: 1px solid rgba(22,199,132,0.16);
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #16c784;
  box-shadow: 0 0 0 6px rgba(22,199,132,0.12);
}

.hero-badge {
  background: rgba(212, 169, 90, 0.1);
  color: #f1d089;
  border: 1px solid rgba(212,169,90,0.22);
}

.hero-main-copy {
  position: relative;
  z-index: 2;
  margin-top: 8px;
}

.field-label {
  display: block;
  font-size: 0.72rem;
  color: rgba(169, 176, 195, 0.9);
  margin-bottom: 12px;
}

.hero-balance {
  font-size: clamp(2.6rem, 2.6vw, 4rem);
  line-height: 1;
  font-weight: 800;
  letter-spacing: -0.05em;
  color: #ffffff;
}

.hero-trend-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
}

.trend-pill {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 800;
}

.trend-pill.positive {
  background: rgba(22, 199, 132, 0.12);
  color: #7cf2c0;
}

.trend-copy {
  color: rgba(169, 176, 195, 0.95);
  font-size: 0.72rem;
}

.hero-canvas-wrap {
  position: absolute;
  inset: 105px 0 110px 0;
  z-index: 1;
  pointer-events: none;
}

.hero-canvas-wrap canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.hero-metrics {
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-top: auto;
}

.metric-box {
  padding: 12px 12px 10px;
  border-radius: 14px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metric-box span {
  font-size: 0.66rem;
  color: rgba(169, 176, 195, 0.95);
}

.metric-box strong {
  font-size: 1.02rem;
  color: #fff;
  font-weight: 700;
  letter-spacing: -0.03em;
}

.metric-box strong.positive {
  color: #7cf2c0;
}
</style>
