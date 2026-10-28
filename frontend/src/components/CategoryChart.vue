<script setup lang="ts">
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  LinearScale,
  Tooltip,
  type ChartData,
  type ChartOptions,
  type TooltipItem,
} from 'chart.js'
import type { CategoryStats } from '../types/dataset'

// Chart.js is tree-shakeable: only the registered parts end up in the bundle.
ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip)

const props = defineProps<{
  stats: CategoryStats[]
}>()

// The chart draws on a canvas, which cannot use var(...), so the color is
// read once from style.css.
const palette = ['#83F9AC', '#30C6F3', '#2DA7D7', '#69CDA3', '#205B85', '#213F69']

function categoryColor(index: number): string {
  const baseColor = palette[index % palette.length]

  const cycle = Math.floor(index / palette.length)

  if (cycle === 0) return baseColor

  // Adjust the lightness for additional categories
  const hueShift = cycle * 7

  // Requires a helper to convert HEX to HSL
  const { h, s, l } = hexToHsl(baseColor)

  const hue = (h + hueShift) % 360
  const lightness = Math.min(85, l + cycle * 8)

  return `hsl(${hue}, ${s}%, ${lightness}%)`
}

const chartData = computed<ChartData<'bar'>>(() => ({
  labels: props.stats.map((s) => s.category),
  datasets: [
    {
      label: 'Average value',
      data: props.stats.map((s) => s.avg),
      backgroundColor: props.stats.map((_, i) => categoryColor(i)),
      borderRadius: 4,
    },
  ],
}))

const format = (n: number) => n.toLocaleString(undefined, { maximumFractionDigits: 3 })

// An average hides the spread of the values, so the tooltip adds the
// count and range of each category.
const options: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    tooltip: {
      callbacks: {
        label: (item: TooltipItem<'bar'>) => {
          const s = props.stats[item.dataIndex]
          return [
            `Average: ${format(s.avg)}`,
            `Min: ${format(s.min)}`,
            `Max: ${format(s.max)}`,
            `Records: ${s.count}`,
          ]
        },
      },
    },
  },
  scales: {
    y: { title: { display: true, text: 'Average value' } },
  },
}
function hexToHsl(hex: string): { h: number; s: number; l: number } {
  // Convert HEX to RGB (0–255)
  const r = parseInt(hex.slice(1, 3), 16) / 255
  const g = parseInt(hex.slice(3, 5), 16) / 255
  const b = parseInt(hex.slice(5, 7), 16) / 255

  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  const delta = max - min

  // Calculate lightness
  let h = 0
  let s = 0
  const l = (max + min) / 2

  if (delta !== 0) {
    // Calculate saturation
    s = delta / (1 - Math.abs(2 * l - 1))

    // Calculate hue
    switch (max) {
      case r:
        h = ((g - b) / delta) % 6
        break
      case g:
        h = (b - r) / delta + 2
        break
      case b:
        h = (r - g) / delta + 4
        break
    }

    h *= 60
  }

  // Normalize hue to 0–360
  h = (h + 360) % 360

  return {
    h: Math.round(h),
    s: Math.round(s * 100),
    l: Math.round(l * 100),
  }
}
</script>

<template>
  <div class="category-chart">
    <Bar :data="chartData" :options="options" />
  </div>
</template>

<style scoped>
.category-chart {
  /* Chart.js sizes the canvas to its container (maintainAspectRatio: false). */
  position: relative;
  height: 280px;
  padding: 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
}
</style>
