<script setup lang="ts">
import {computed, nextTick, onBeforeUnmount, onMounted, ref, watch,} from 'vue'

import {normalizeDigits, toPersianDigits,} from '@/utils/formatters'

import {serializePersianDateInput,} from '@/utils/persianDateInput'

import AppIcon from '@/components/ui/AppIcon.vue'

interface Props {
  modelValue: string
  label?: string
  placeholder?: string
  error?: string
  disabled?: boolean
}

const props = withDefaults(
    defineProps<Props>(),
    {
      label: '',
      placeholder: '۱۴۰۵/۰۶/۰۱',
      error: '',
      disabled: false,
    },
)

const emit = defineEmits<{
  (
      event: 'update:modelValue',
      value: string,
  ): void

  (
      event: 'blur',
  ): void
}>()

const root = ref<HTMLElement | null>(null)
const input = ref<HTMLInputElement | null>(null)

const isOpen = ref(false)

const currentYear = ref(1405)
const currentMonth = ref(7)

const weekdays = [
  'ش',
  'ی',
  'د',
  'س',
  'چ',
  'پ',
  'ج',
]

const monthNames = [
  'فروردین',
  'اردیبهشت',
  'خرداد',
  'تیر',
  'مرداد',
  'شهریور',
  'مهر',
  'آبان',
  'آذر',
  'دی',
  'بهمن',
  'اسفند',
]

const localValue = ref(props.modelValue)

watch(
    () => props.modelValue,
    (value) => {
      localValue.value = value
    },
)

function parsePersianValue(
    value: string,
): {
  year: number
  month: number
  day: number
} | null {
  const normalized = normalizeDigits(
      value.trim(),
  )

  const match = normalized.match(
      /^(\d{4})[/-](\d{1,2})[/-](\d{1,2})$/,
  )

  if (!match) {
    return null
  }

  const year = Number(match[1])
  const month = Number(match[2])
  const day = Number(match[3])

  if (
      !year
      || month < 1
      || month > 12
      || day < 1
      || day > 31
  ) {
    return null
  }

  return {
    year,
    month,
    day,
  }
}

function jalaliToIso(
    year: number,
    month: number,
    day: number,
): string {
  const value =
      `${year}/${String(month).padStart(2, '0')}/${String(day).padStart(2, '0')}`

  return (
      serializePersianDateInput(value)
      || ''
  )
}

function isoToPersianParts(
    iso: string,
): {
  year: number
  month: number
  day: number
} | null {
  const date = new Date(iso)

  if (Number.isNaN(date.getTime())) {
    return null
  }

  const parts = new Intl.DateTimeFormat(
      'fa-IR-u-ca-persian',
      {
        year: 'numeric',
        month: 'numeric',
        day: 'numeric',
        timeZone: 'UTC',
      },
  ).formatToParts(date)

  const yearRaw =
      parts.find(
          (part) =>
              part.type === 'year',
      )?.value || ''

  const monthRaw =
      parts.find(
          (part) =>
              part.type === 'month',
      )?.value || ''

  const dayRaw =
      parts.find(
          (part) =>
              part.type === 'day',
      )?.value || ''

  const year = Number(
      normalizeDigits(yearRaw),
  )

  const month = Number(
      normalizeDigits(monthRaw),
  )

  const day = Number(
      normalizeDigits(dayRaw),
  )

  if (
      !Number.isFinite(year)
      || !Number.isFinite(month)
      || !Number.isFinite(day)
  ) {
    return null
  }

  return {
    year,
    month,
    day,
  }
}

function isoToWeekday(
    iso: string,
): number {
  const date = new Date(iso)

  if (Number.isNaN(date.getTime())) {
    return 0
  }

  // JS:
  // Sunday = 0
  // Monday = 1
  // ...
  //
  // Persian calendar:
  // Saturday is first column.
  //
  // Convert Sunday...Friday => 1...6
  // Saturday => 0

  return (
      date.getUTCDay() + 1
  ) % 7
}

const monthDays = computed(() => {
  const firstIso = jalaliToIso(
      currentYear.value,
      currentMonth.value,
      1,
  )

  if (!firstIso) {
    return []
  }

  const nextMonth =
      currentMonth.value === 12
          ? {
            year: currentYear.value + 1,
            month: 1,
          }
          : {
            year: currentYear.value,
            month: currentMonth.value + 1,
          }

  const nextMonthIso =
      jalaliToIso(
          nextMonth.year,
          nextMonth.month,
          1,
      )

  if (!nextMonthIso) {
    return []
  }

  const start = new Date(
      `${firstIso}T00:00:00Z`,
  )

  const end = new Date(
      `${nextMonthIso}T00:00:00Z`,
  )

  const count = Math.round(
      (
          end.getTime()
          - start.getTime()
      )
      / (
          24 * 60 * 60 * 1000
      ),
  )

  return Array.from(
      {
        length: count,
      },
      (_, index) => {
        const date = new Date(
            start.getTime()
            + index
            * 24
            * 60
            * 60
            * 1000,
        )

        const iso =
            date
                .toISOString()
                .slice(0, 10)

        const weekday =
            isoToWeekday(iso)

        return {
          day: index + 1,
          iso,
          weekday,
        }
      },
  )
})

const calendarCells = computed(() => {
  const firstIso = jalaliToIso(
      currentYear.value,
      currentMonth.value,
      1,
  )

  if (!firstIso) {
    return []
  }

  const firstWeekday =
      isoToWeekday(firstIso)

  return [
    ...Array.from(
        {
          length: firstWeekday,
        },
        () => null,
    ),
    ...monthDays.value,
  ]
})

const selectedDate = computed(() => {
  return parsePersianValue(
      localValue.value,
  )
})

const today = computed(() => {
  const now = new Date()

  const parts = new Intl.DateTimeFormat(
      'fa-IR-u-ca-persian',
      {
        year: 'numeric',
        month: 'numeric',
        day: 'numeric',
        timeZone: 'Asia/Tehran',
      },
  ).formatToParts(now)

  const yearRaw =
      parts.find(
          (part) =>
              part.type === 'year',
      )?.value || ''

  const monthRaw =
      parts.find(
          (part) =>
              part.type === 'month',
      )?.value || ''

  const dayRaw =
      parts.find(
          (part) =>
              part.type === 'day',
      )?.value || ''

  return {
    year: Number(
        normalizeDigits(yearRaw),
    ),
    month: Number(
        normalizeDigits(monthRaw),
    ),
    day: Number(
        normalizeDigits(dayRaw),
    ),
  }
})

function isSelected(
    day: number,
): boolean {
  return Boolean(
      selectedDate.value
      && selectedDate.value.year
      === currentYear.value
      && selectedDate.value.month
      === currentMonth.value
      && selectedDate.value.day
      === day,
  )
}

function isToday(
    day: number,
): boolean {
  return (
      today.value.year
      === currentYear.value
      && today.value.month
      === currentMonth.value
      && today.value.day
      === day
  )
}

function emitValue(
    value: string,
): void {
  localValue.value =
      toPersianDigits(value)

  emit(
      'update:modelValue',
      localValue.value,
  )
}

function selectDay(
  day: number,
): void {
  const value =
    `${currentYear.value}/${String(currentMonth.value).padStart(2, '0')}/${String(day).padStart(2, '0')}`

  localValue.value =
    toPersianDigits(value)

  emit(
    'update:modelValue',
    localValue.value,
  )

  isOpen.value = false
}

function goPreviousMonth(): void {
  if (currentMonth.value === 1) {
    currentMonth.value = 12
    currentYear.value -= 1
  } else {
    currentMonth.value -= 1
  }
}

function goNextMonth(): void {
  if (currentMonth.value === 12) {
    currentMonth.value = 1
    currentYear.value += 1
  } else {
    currentMonth.value += 1
  }
}

function goToday(): void {
  currentYear.value =
      today.value.year

  currentMonth.value =
      today.value.month

  selectDay(
      today.value.day,
  )
}

function openCalendar(): void {
  if (props.disabled) {
    return
  }

  const parsed =
      parsePersianValue(
          localValue.value,
      )

  if (parsed) {
    currentYear.value =
        parsed.year

    currentMonth.value =
        parsed.month
  } else {
    currentYear.value =
        today.value.year

    currentMonth.value =
        today.value.month
  }

  isOpen.value = true
}

function normalizeInput(): void {
  const raw = normalizeDigits(
      localValue.value.trim(),
  )

  if (!raw) {
    localValue.value = ''

    emit(
        'update:modelValue',
        '',
    )

    emit('blur')
    return
  }

  /*
   * تاریخ ورودی همیشه شمسی است.
   *
   * ابتدا فقط اعتبارسنجی/نرمال‌سازی می‌کنیم.
   * نباید تاریخ شمسی را به Date تبدیل کنیم،
   * چون ممکن است ۱۴۰۵/۰۷/۲۳ به‌عنوان سال میلادی
   * تفسیر شود و نتیجه‌ی اشتباه مثل ۷۸۴/۰۴/۲۳ تولید کند.
   */
  const normalized = raw
      .replace(/-/g, '/')
      .replace(
          /\/+/g,
          '/',
      )

  const match = normalized.match(
      /^(\d{4})\/(\d{1,2})\/(\d{1,2})$/,
  )

  if (match) {
    const year = Number(match[1])
    const month = Number(match[2])
    const day = Number(match[3])

    if (
        year >= 1200
        && year <= 1700
        && month >= 1
        && month <= 12
        && day >= 1
        && day <= 31
    ) {
      const value =
          `${String(year).padStart(4, '0')}/${
              String(month).padStart(2, '0')
          }/${
              String(day).padStart(2, '0')
          }`

      localValue.value =
          toPersianDigits(value)

      emit(
          'update:modelValue',
          localValue.value,
      )

      emit('blur')
      return
    }
  }

  localValue.value =
      toPersianDigits(normalized)

  emit(
      'update:modelValue',
      localValue.value,
  )

  emit('blur')
}

function clearValue(): void {
  localValue.value = ''

  emit(
      'update:modelValue',
      '',
  )

  isOpen.value = false

  void nextTick(() => {
    input.value?.focus()
  })
}

function handleOutsideClick(
    event: MouseEvent,
): void {
  if (
      root.value
      && !root.value.contains(
          event.target as Node,
      )
  ) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener(
      'mousedown',
      handleOutsideClick,
  )
})

onBeforeUnmount(() => {
  document.removeEventListener(
      'mousedown',
      handleOutsideClick,
  )
})
</script>

<template>
  <div
      ref="root"
      class="persian-date-picker"
  >
    <label
        v-if="label"
        class="date-picker-label"
    >
      {{ label }}
    </label>

    <div
        class="date-input-wrap"
        :class="{
          'has-error': !!error,
          'is-disabled': disabled,
          'is-open': isOpen,
        }"
    >
      <input
          ref="input"
          v-model="localValue"
          class="date-input"
          type="text"
          inputmode="numeric"
          dir="ltr"
          maxlength="10"
          :placeholder="placeholder"
          :disabled="disabled"
          @focus="openCalendar"
          @blur="normalizeInput"
          @keydown.esc="isOpen = false"
      />

      <button
          class="calendar-button"
          type="button"
          :disabled="disabled"
          aria-label="انتخاب تاریخ"
          @mousedown.prevent
          @click="openCalendar"
      >
        <AppIcon
            name="calendar"
            :size="17"
        />
      </button>

      <button
          v-if="localValue"
          class="clear-button"
          type="button"
          aria-label="پاک کردن تاریخ"
          @mousedown.prevent
          @click="clearValue"
      >
        <AppIcon
            name="close"
            :size="14"
        />
      </button>
    </div>

    <small
        v-if="error"
        class="date-picker-error"
    >
      {{ error }}
    </small>

    <div
        v-if="isOpen"
        class="calendar-popover"
        dir="rtl"
    >
      <div class="calendar-header">
        <button
            type="button"
            class="calendar-nav"
            aria-label="ماه قبل"
            @click="goPreviousMonth"
        >
          <AppIcon
              name="chevronRight"
              :size="16"
          />
        </button>

        <strong>
          {{ monthNames[currentMonth - 1] }}
          {{ toPersianDigits(currentYear) }}
        </strong>

        <button
            type="button"
            class="calendar-nav"
            aria-label="ماه بعد"
            @click="goNextMonth"
        >
          <AppIcon
              name="chevronLeft"
              :size="16"
          />
        </button>
      </div>

      <div class="calendar-weekdays">
        <span
            v-for="weekday in weekdays"
            :key="weekday"
        >
          {{ weekday }}
        </span>
      </div>

      <div class="calendar-grid">
        <span
            v-for="(cell, index) in calendarCells"
            :key="cell?.iso ?? `empty-${index}`"
            class="calendar-cell"
        >
          <button
              v-if="cell"
              type="button"
              class="calendar-day"
              :class="{
                'is-selected':
                  isSelected(cell.day),
                'is-today':
                  isToday(cell.day),
              }"
              @click="
                selectDay(cell.day)
              "
          >
            {{ toPersianDigits(cell.day) }}
          </button>
        </span>
      </div>

      <div class="calendar-footer">
        <button
            type="button"
            class="calendar-today-button"
            @click="goToday"
        >
          امروز
        </button>

        <button
            v-if="localValue"
            type="button"
            class="calendar-clear-button"
            @click="clearValue"
        >
          پاک کردن
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.persian-date-picker {
  position: relative;
  min-width: 0;
}

.date-picker-label {
  display: block;
  margin-bottom: .45rem;
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  font-weight: 600;
}

.date-input-wrap {
  position: relative;
  display: flex;
  min-height: var(--control-height);
  align-items: center;
  border: 1px solid var(--control-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  transition: border-color .16s ease,
  box-shadow .16s ease;
}

.date-input-wrap:hover {
  border-color: var(--color-border-hover);
}

.date-input-wrap:focus-within,
.date-input-wrap.is-open {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-focus);
}

.date-input-wrap.has-error {
  border-color: var(--color-danger);
}

.date-input-wrap.is-disabled {
  opacity: .65;
  cursor: not-allowed;
}

.date-input {
  width: 100%;
  min-width: 0;
  min-height: calc(
      var(--control-height) - 2px
  );
  padding: 0 2.7rem 0 2.4rem;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--color-text-primary);
  font: inherit;
}

.date-input::placeholder {
  color: var(--color-text-muted);
}

.calendar-button,
.clear-button {
  position: absolute;
  top: 50%;
  display: grid;
  width: 2.1rem;
  height: 2.1rem;
  place-items: center;
  border: 0;
  transform: translateY(-50%);
  background: transparent;
  cursor: pointer;
}

.calendar-button {
  right: .35rem;
  color: var(--color-primary);
}

.clear-button {
  left: .35rem;
  color: var(--color-text-muted);
}

.calendar-button:hover {
  color: var(--color-text-primary);
}

.clear-button:hover {
  color: var(--color-danger);
}

.calendar-button:disabled {
  cursor: not-allowed;
}

.date-picker-error {
  display: block;
  margin-top: .35rem;
  color: var(--color-danger);
  font-size: .68rem;
  line-height: 1.5;
}

.calendar-popover {
  position: absolute;
  z-index: 9999;

  top: calc(100% + .5rem);
  right: 0;

  width: min(20rem, 92vw);
  padding: .8rem;

  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);

  background: #0b1220;
  background-color: #0b1220;

  box-shadow: 0 18px 45px rgba(0, 0, 0, .35),
  0 4px 14px rgba(0, 0, 0, .2);

  isolation: isolate;
  overflow: hidden;
}

.calendar-header {
  display: grid;
  grid-template-columns: 2rem 1fr 2rem;
  align-items: center;
  gap: .4rem;
  margin-bottom: .7rem;
}

.calendar-header strong {
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  text-align: center;
}

.calendar-nav {
  display: grid;
  width: 2rem;
  height: 2rem;
  place-items: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface-2);
  color: var(--color-text-secondary);
  cursor: pointer;
}

.calendar-nav:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.calendar-weekdays,
.calendar-grid {
  display: grid;
  grid-template-columns:
    repeat(7, minmax(0, 1fr));
  gap: .2rem;
}

.calendar-weekdays {
  margin-bottom: .25rem;
}

.calendar-weekdays span {
  padding: .25rem 0;
  color: var(--color-text-muted);
  font-size: .66rem;
  font-weight: 650;
  text-align: center;
}

.calendar-cell {
  display: grid;
  min-height: 2.3rem;
  place-items: center;
}

.calendar-day {
  display: grid;
  width: 2.25rem;
  height: 2.25rem;
  place-items: center;
  border: 1px solid transparent;
  border-radius: .65rem;
  background: transparent;
  color: var(--color-text-secondary);
  font: inherit;
  font-size: var(--font-size-xs);
  cursor: pointer;
}

.calendar-day:hover {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.calendar-day.is-today {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.calendar-day.is-selected {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: var(--on-primary);
}

.calendar-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: .5rem;
  margin-top: .7rem;
  padding-top: .7rem;
  border-top: 1px solid var(--color-border-soft);
}

.calendar-today-button,
.calendar-clear-button {
  min-height: 2.2rem;
  padding-inline: .7rem;
  border-radius: var(--radius-sm);
  font: inherit;
  font-size: .68rem;
  font-weight: 650;
  cursor: pointer;
}

.calendar-today-button {
  border: 1px solid var(--color-primary);
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.calendar-clear-button {
  border: 1px solid var(--color-border);
  background: var(--color-surface-2);
  color: var(--color-text-muted);
}

:global(:root[data-theme='light']) .calendar-popover {
  background: #ffffff;
  background-color: #ffffff;

  box-shadow: 0 18px 45px rgba(15, 23, 42, .16),
  0 4px 14px rgba(15, 23, 42, .10);
}
</style>