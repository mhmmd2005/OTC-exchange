<script setup lang="ts">
import { computed } from 'vue'

interface ReedSolomonBlock {
  count: number
  totalCodewords: number
  dataCodewords: number
}

const props = withDefaults(defineProps<{
  value: string
  size?: number
  label?: string
}>(), {
  size: 168,
  label: 'کد QR آدرس واریز',
})

/*
 * QR Model 2, byte mode, error-correction level L. Versions 1–10 cover
 * payloads up to 271 UTF-8 bytes, which comfortably includes wallet addresses.
 * Keeping this encoder local makes the address QR available offline and avoids
 * sending a deposit address to an external image service.
 */
const BLOCKS: Readonly<Record<number, readonly ReedSolomonBlock[]>> = {
  1: [{ count: 1, totalCodewords: 26, dataCodewords: 19 }],
  2: [{ count: 1, totalCodewords: 44, dataCodewords: 34 }],
  3: [{ count: 1, totalCodewords: 70, dataCodewords: 55 }],
  4: [{ count: 1, totalCodewords: 100, dataCodewords: 80 }],
  5: [{ count: 1, totalCodewords: 134, dataCodewords: 108 }],
  6: [{ count: 2, totalCodewords: 86, dataCodewords: 68 }],
  7: [{ count: 2, totalCodewords: 98, dataCodewords: 78 }],
  8: [{ count: 2, totalCodewords: 121, dataCodewords: 97 }],
  9: [{ count: 2, totalCodewords: 146, dataCodewords: 116 }],
  10: [
    { count: 2, totalCodewords: 86, dataCodewords: 68 },
    { count: 2, totalCodewords: 87, dataCodewords: 69 },
  ],
}

const ALIGNMENT_CENTERS: Readonly<Record<number, readonly number[]>> = {
  1: [],
  2: [6, 18],
  3: [6, 22],
  4: [6, 26],
  5: [6, 30],
  6: [6, 34],
  7: [6, 22, 38],
  8: [6, 24, 42],
  9: [6, 26, 46],
  10: [6, 28, 50],
}

const GF_EXP = new Array<number>(512).fill(0)
const GF_LOG = new Array<number>(256).fill(0)
let fieldValue = 1
for (let index = 0; index < 255; index += 1) {
  GF_EXP[index] = fieldValue
  GF_LOG[fieldValue] = index
  fieldValue <<= 1
  if ((fieldValue & 0x100) !== 0) fieldValue ^= 0x11d
}
for (let index = 255; index < GF_EXP.length; index += 1) GF_EXP[index] = GF_EXP[index - 255] ?? 0

function multiply(left: number, right: number): number {
  if (left === 0 || right === 0) return 0
  return GF_EXP[(GF_LOG[left] ?? 0) + (GF_LOG[right] ?? 0)] ?? 0
}

function generatorPolynomial(degree: number): number[] {
  let polynomial = [1]
  for (let index = 0; index < degree; index += 1) {
    const next = new Array<number>(polynomial.length + 1).fill(0)
    const root = GF_EXP[index] ?? 0
    for (let term = 0; term < polynomial.length; term += 1) {
      const coefficient = polynomial[term] ?? 0
      next[term] = (next[term] ?? 0) ^ coefficient
      next[term + 1] = (next[term + 1] ?? 0) ^ multiply(coefficient, root)
    }
    polynomial = next
  }
  return polynomial
}

function errorCorrection(data: readonly number[], length: number): number[] {
  const generator = generatorPolynomial(length)
  const remainder = new Array<number>(length).fill(0)
  for (const byte of data) {
    const factor = byte ^ (remainder[0] ?? 0)
    remainder.shift()
    remainder.push(0)
    for (let index = 0; index < length; index += 1) {
      remainder[index] = (remainder[index] ?? 0) ^ multiply(generator[index + 1] ?? 0, factor)
    }
  }
  return remainder
}

function pushBits(target: number[], value: number, length: number): void {
  for (let bit = length - 1; bit >= 0; bit -= 1) target.push((value >>> bit) & 1)
}

function dataCapacity(version: number): number {
  return (BLOCKS[version] ?? []).reduce(
    (total, block) => total + block.count * block.dataCodewords,
    0,
  )
}

function selectVersion(byteLength: number): number | null {
  for (let version = 1; version <= 10; version += 1) {
    const countLength = version < 10 ? 8 : 16
    if (byteLength < 2 ** countLength && 4 + countLength + byteLength * 8 <= dataCapacity(version) * 8) {
      return version
    }
  }
  return null
}

function createData(bytes: readonly number[], version: number): number[] {
  const capacity = dataCapacity(version)
  const bits: number[] = []
  pushBits(bits, 0b0100, 4)
  pushBits(bits, bytes.length, version < 10 ? 8 : 16)
  for (const byte of bytes) pushBits(bits, byte, 8)

  const remaining = capacity * 8 - bits.length
  for (let index = 0; index < Math.min(4, remaining); index += 1) bits.push(0)
  while (bits.length % 8 !== 0) bits.push(0)

  const data: number[] = []
  for (let offset = 0; offset < bits.length; offset += 8) {
    let byte = 0
    for (let bit = 0; bit < 8; bit += 1) byte = (byte << 1) | (bits[offset + bit] ?? 0)
    data.push(byte)
  }
  for (let index = 0; data.length < capacity; index += 1) data.push(index % 2 === 0 ? 0xec : 0x11)
  return data
}

function createCodewords(data: readonly number[], version: number): number[] {
  const dataBlocks: number[][] = []
  const correctionBlocks: number[][] = []
  let offset = 0

  for (const group of BLOCKS[version] ?? []) {
    for (let blockIndex = 0; blockIndex < group.count; blockIndex += 1) {
      const blockData = data.slice(offset, offset + group.dataCodewords)
      offset += group.dataCodewords
      dataBlocks.push(blockData)
      correctionBlocks.push(errorCorrection(blockData, group.totalCodewords - group.dataCodewords))
    }
  }

  const result: number[] = []
  const maxDataLength = Math.max(...dataBlocks.map((block) => block.length))
  for (let index = 0; index < maxDataLength; index += 1) {
    for (const block of dataBlocks) if (block[index] !== undefined) result.push(block[index])
  }
  const correctionLength = correctionBlocks[0]?.length ?? 0
  for (let index = 0; index < correctionLength; index += 1) {
    for (const block of correctionBlocks) result.push(block[index] ?? 0)
  }
  return result
}

type Matrix = Array<Array<boolean | null>>

function drawFinder(matrix: Matrix, centerX: number, centerY: number): void {
  const size = matrix.length
  for (let deltaY = -4; deltaY <= 4; deltaY += 1) {
    for (let deltaX = -4; deltaX <= 4; deltaX += 1) {
      const x = centerX + deltaX
      const y = centerY + deltaY
      if (x < 0 || y < 0 || x >= size || y >= size) continue
      const distance = Math.max(Math.abs(deltaX), Math.abs(deltaY))
      matrix[y]![x] = distance === 3 || distance <= 1
    }
  }
}

function drawAlignment(matrix: Matrix, centerX: number, centerY: number): void {
  if (matrix[centerY]?.[centerX] !== null) return
  for (let deltaY = -2; deltaY <= 2; deltaY += 1) {
    for (let deltaX = -2; deltaX <= 2; deltaX += 1) {
      matrix[centerY + deltaY]![centerX + deltaX] = Math.max(Math.abs(deltaX), Math.abs(deltaY)) !== 1
    }
  }
}

function bchDigit(value: number): number {
  let digit = 0
  let current = value
  while (current !== 0) {
    digit += 1
    current >>>= 1
  }
  return digit
}

function formatBits(mask: number): number {
  const generator = 0x537
  const data = (0b01 << 3) | mask
  let remainder = data << 10
  while (bchDigit(remainder) - bchDigit(generator) >= 0) {
    remainder ^= generator << (bchDigit(remainder) - bchDigit(generator))
  }
  return ((data << 10) | remainder) ^ 0x5412
}

function versionBits(version: number): number {
  const generator = 0x1f25
  let remainder = version << 12
  while (bchDigit(remainder) - bchDigit(generator) >= 0) {
    remainder ^= generator << (bchDigit(remainder) - bchDigit(generator))
  }
  return (version << 12) | remainder
}

function writeFormat(matrix: Matrix, mask: number): void {
  const size = matrix.length
  const bits = formatBits(mask)
  for (let index = 0; index < 15; index += 1) {
    const dark = ((bits >>> index) & 1) === 1
    const verticalY = index < 6 ? index : index < 8 ? index + 1 : size - 15 + index
    const horizontalX = index < 8 ? size - index - 1 : index === 8 ? 7 : 14 - index
    matrix[verticalY]![8] = dark
    matrix[8]![horizontalX] = dark
  }
  matrix[size - 8]![8] = true
}

function writeVersion(matrix: Matrix, version: number): void {
  if (version < 7) return
  const size = matrix.length
  const bits = versionBits(version)
  for (let index = 0; index < 18; index += 1) {
    const dark = ((bits >>> index) & 1) === 1
    matrix[Math.floor(index / 3)]![index % 3 + size - 11] = dark
    matrix[index % 3 + size - 11]![Math.floor(index / 3)] = dark
  }
}

function shouldMask(row: number, column: number): boolean {
  return (row + column) % 2 === 0
}

function makeMatrix(codewords: readonly number[], version: number): boolean[][] {
  const size = version * 4 + 17
  const matrix: Matrix = Array.from({ length: size }, () => new Array<boolean | null>(size).fill(null))

  drawFinder(matrix, 3, 3)
  drawFinder(matrix, size - 4, 3)
  drawFinder(matrix, 3, size - 4)

  for (let index = 8; index < size - 8; index += 1) {
    if (matrix[6]?.[index] === null) matrix[6]![index] = index % 2 === 0
    if (matrix[index]?.[6] === null) matrix[index]![6] = index % 2 === 0
  }

  for (const centerY of ALIGNMENT_CENTERS[version] ?? []) {
    for (const centerX of ALIGNMENT_CENTERS[version] ?? []) drawAlignment(matrix, centerX, centerY)
  }

  writeFormat(matrix, 0)
  writeVersion(matrix, version)

  let byteIndex = 0
  let bitIndex = 7
  let row = size - 1
  let direction = -1
  for (let right = size - 1; right > 0; right -= 2) {
    if (right === 6) right -= 1
    while (row >= 0 && row < size) {
      for (let offset = 0; offset < 2; offset += 1) {
        const column = right - offset
        if (matrix[row]?.[column] !== null) continue
        const source = codewords[byteIndex] ?? 0
        let dark = ((source >>> bitIndex) & 1) === 1
        if (shouldMask(row, column)) dark = !dark
        matrix[row]![column] = dark
        bitIndex -= 1
        if (bitIndex < 0) {
          byteIndex += 1
          bitIndex = 7
        }
      }
      row += direction
    }
    row -= direction
    direction = -direction
  }

  return matrix.map((line) => line.map((module) => module ?? false))
}

const qr = computed(() => {
  const bytes = Array.from(new TextEncoder().encode(props.value))
  const version = selectVersion(bytes.length)
  if (version === null) return null
  const matrix = makeMatrix(createCodewords(createData(bytes, version), version), version)
  const quietZone = 4
  const viewBoxSize = matrix.length + quietZone * 2
  const path = matrix.flatMap((row, y) => row.map((dark, x) => dark ? `M${x + quietZone} ${y + quietZone}h1v1h-1z` : '')).join('')
  return { path, viewBoxSize }
})
</script>

<template>
  <svg
    v-if="qr"
    class="qr-code"
    :width="size"
    :height="size"
    :viewBox="`0 0 ${qr.viewBoxSize} ${qr.viewBoxSize}`"
    role="img"
    :aria-label="label"
    shape-rendering="crispEdges"
  >
    <rect :width="qr.viewBoxSize" :height="qr.viewBoxSize" fill="#fff" />
    <path :d="qr.path" fill="#06101c" />
  </svg>
  <div v-else class="qr-code qr-code--unavailable" :style="{ width: `${size}px`, height: `${size}px` }" role="img" :aria-label="label">
    <span aria-hidden="true">QR</span>
  </div>
</template>

<style scoped>
.qr-code { display: block; max-width: 100%; border-radius: var(--radius-sm); }
.qr-code--unavailable { display: grid; border: 1px dashed var(--color-border-hover); background: var(--color-surface-2); color: var(--color-text-muted); font-size: var(--font-size-sm); place-items: center; }
</style>
