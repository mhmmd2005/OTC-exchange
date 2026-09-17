<script setup lang="ts">
import {computed, onMounted, ref,} from 'vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppModal from '@/components/ui/AppModal.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import KycApplicationDetailPage from './KycApplicationDetailPage.vue'
import {type AdminKycApplication, kycAdminService,} from '@/services/admin/kycAdmin.service'

const applications = ref<AdminKycApplication[]>([])
const selectedApplication =
    ref<AdminKycApplication | null>(null)

const selectedIds = ref<number[]>([])
const deleteTargets = ref<number[]>([])

const deleteMode = ref(false)

const loading = ref(true)
const loadingDetail = ref(false)
const deleting = ref(false)
const error = ref('')
const search = ref('')

const filteredApplications = computed(() => {
  const query = search.value
      .trim()
      .toLowerCase()

  if (!query) {
    return applications.value
  }

  return applications.value.filter((item) =>
      [
        item.phoneNumber,
        item.email,
        item.firstName,
        item.lastName,
        item.nationalId,
      ]
          .filter(Boolean)
          .some((value) =>
              String(value)
                  .toLowerCase()
                  .includes(query),
          ),
  )
})

const selectedCount = computed(
    () => selectedIds.value.length,
)

const allVisibleSelected = computed(() => {
  if (!filteredApplications.value.length) {
    return false
  }

  return filteredApplications.value.every(
      (item) =>
          selectedIds.value.includes(item.id),
  )
})

const pendingCount = computed(
    () =>
        applications.value.filter(
            (item) =>
                item.status === 'pending' ||
                item.basicInfoStatus === 'pending' ||
                item.identityStatus === 'pending' ||
                getBankStatus(item) === 'pending',
        ).length,
)

const approvedCount = computed(
    () =>
        applications.value.filter(
            (item) => item.status === 'approved',
        ).length,
)

const rejectedCount = computed(
    () =>
        applications.value.filter(
            (item) => item.status === 'rejected',
        ).length,
)

function readableError(
    errorValue: unknown,
    fallback: string,
): string {
  return errorValue instanceof Error
      ? errorValue.message
      : fallback
}

function getBankStatus(
    application: AdminKycApplication,
): string {
  if (!application.bankAccounts.length) {
    return 'not_started'
  }

  if (
      application.bankAccounts.some(
          (account) =>
              account.status === 'pending',
      )
  ) {
    return 'pending'
  }

  if (
      application.bankAccounts.some(
          (account) =>
              account.status === 'verified',
      )
  ) {
    return 'verified'
  }

  if (
      application.bankAccounts.some(
          (account) =>
              account.status === 'rejected',
      )
  ) {
    return 'rejected'
  }

  return 'not_started'
}

function getUserName(
    application: AdminKycApplication,
): string {
  return (
      `${application.firstName} ${application.lastName}`.trim() ||
      application.phoneNumber ||
      'کاربر'
  )
}

function getUserInitials(
    application: AdminKycApplication,
): string {
  const name =
      `${application.firstName} ${application.lastName}`.trim()

  if (!name) {
    return '؟'
  }

  return name.slice(0, 2)
}

function enterDeleteMode(): void {
  deleteMode.value = true
  selectedIds.value = []
}

function exitDeleteMode(): void {
  if (deleting.value) {
    return
  }

  deleteMode.value = false
  selectedIds.value = []
}

function isSelected(id: number): boolean {
  return selectedIds.value.includes(id)
}

function toggleSelection(id: number): void {
  if (isSelected(id)) {
    selectedIds.value =
        selectedIds.value.filter(
            (item) => item !== id,
        )

    return
  }

  selectedIds.value = [
    ...selectedIds.value,
    id,
  ]
}

function toggleSelectAll(): void {
  const visibleIds =
      filteredApplications.value.map(
          (item) => item.id,
      )

  if (allVisibleSelected.value) {
    selectedIds.value =
        selectedIds.value.filter(
            (id) => !visibleIds.includes(id),
        )

    return
  }

  selectedIds.value = Array.from(
      new Set([
        ...selectedIds.value,
        ...visibleIds,
      ]),
  )
}

function openDeleteModal(
    ids: number[],
): void {
  if (!ids.length || deleting.value) {
    return
  }

  deleteTargets.value = [...ids]
}

function closeDeleteModal(): void {
  if (deleting.value) {
    return
  }

  deleteTargets.value = []
}

async function confirmDelete(): Promise<void> {
  if (
      !deleteTargets.value.length ||
      deleting.value
  ) {
    return
  }

  deleting.value = true
  error.value = ''

  const targets = [...deleteTargets.value]
  let failedCount = 0

  try {
    for (const id of targets) {
      try {
        await kycAdminService.remove(id)
      } catch {
        failedCount += 1
      }
    }

    if (
        selectedApplication.value &&
        targets.includes(
            selectedApplication.value.id,
        )
    ) {
      selectedApplication.value = null
    }

    deleteTargets.value = []

    await load()

    deleteMode.value = false
    selectedIds.value = []

    if (failedCount > 0) {
      error.value =
          failedCount === targets.length
              ? 'حذف درخواست‌ها انجام نشد.'
              : `${failedCount} درخواست حذف نشد.`
    }
  } finally {
    deleting.value = false
  }
}

async function load(): Promise<void> {
  loading.value = true
  error.value = ''

  try {
    applications.value =
        await kycAdminService.list()

    selectedIds.value =
        selectedIds.value.filter((id) =>
            applications.value.some(
                (item) => item.id === id,
            ),
        )
  } catch (caught) {
    error.value = readableError(
        caught,
        'لیست درخواست‌های احراز هویت بارگیری نشد.',
    )
  } finally {
    loading.value = false
  }
}

async function openApplication(
    id: number,
): Promise<void> {
  loadingDetail.value = true
  error.value = ''

  try {
    selectedApplication.value =
        await kycAdminService.detail(id)
  } catch (caught) {
    error.value = readableError(
        caught,
        'جزئیات درخواست بارگیری نشد.',
    )
  } finally {
    loadingDetail.value = false
  }
}

async function refreshApplication(): Promise<void> {
  if (!selectedApplication.value) {
    await load()
    return
  }

  await openApplication(
      selectedApplication.value.id,
  )

  await load()
}

function closeDetail(): void {
  selectedApplication.value = null
}

onMounted(load)
</script>

<template>
  <div class="kyc-page">
    <section class="kyc-toolbar">
      <div class="kyc-toolbar__copy">
        <span class="eyebrow">
          مدیریت احراز هویت
        </span>

        <h2>درخواست‌های احراز هویت</h2>

        <p>
          بررسی و مدیریت اطلاعات هویتی، مدرک
          شناسایی و حساب‌های بانکی کاربران.
        </p>
      </div>

      <div class="kyc-toolbar__actions">
        <div class="toolbar-search">
          <AppInput
              v-model="search"
              label="جستجو"
              placeholder="نام، موبایل، ایمیل یا کد ملی"
              ltr
          />

          <button
              v-if="search"
              type="button"
              class="toolbar-search__clear"
              aria-label="پاک کردن جستجو"
              @click="search = ''"
          >
            <AppIcon
                name="close"
                :size="15"
            />
          </button>
        </div>

        <AppButton
            variant="secondary"
            size="sm"
            icon="refresh"
            :loading="loading"
            @click="load"
        >
          بروزرسانی
        </AppButton>
      </div>
    </section>

    <section class="overview-grid">
      <div class="overview-card">
        <div class="overview-card__icon primary">
          <AppIcon
              name="verify"
              :size="19"
          />
        </div>

        <div>
          <span>کل درخواست‌ها</span>
          <strong>
            {{ applications.length }}
          </strong>
        </div>
      </div>

      <div class="overview-card">
        <div class="overview-card__icon warning">
          <AppIcon
              name="loader"
              :size="19"
          />
        </div>

        <div>
          <span>در انتظار بررسی</span>
          <strong>
            {{ pendingCount }}
          </strong>
        </div>
      </div>

      <div class="overview-card">
        <div class="overview-card__icon success">
          <AppIcon
              name="check"
              :size="19"
          />
        </div>

        <div>
          <span>تأیید شده</span>
          <strong>
            {{ approvedCount }}
          </strong>
        </div>
      </div>

      <div class="overview-card">
        <div class="overview-card__icon danger">
          <AppIcon
              name="close"
              :size="19"
          />
        </div>

        <div>
          <span>رد شده</span>
          <strong>
            {{ rejectedCount }}
          </strong>
        </div>
      </div>
    </section>

    <div
        v-if="error"
        class="page-notice danger"
        role="alert"
    >
      <AppIcon
          name="warning"
          :size="19"
      />

      <span>{{ error }}</span>

      <AppButton
          variant="secondary"
          size="sm"
          @click="load"
      >
        تلاش مجدد
      </AppButton>
    </div>

    <AppCard
        padding="none"
        class="kyc-list-card"
    >
      <div class="list-toolbar">
        <div class="list-toolbar__left">
          <template v-if="deleteMode">
            <label class="select-all">
              <input
                  type="checkbox"
                  :checked="allVisibleSelected"
                  @change="toggleSelectAll"
              />

              <span>
                انتخاب همه
              </span>
            </label>

            <span
                v-if="selectedCount"
                class="selected-count"
            >
              {{ selectedCount }}
              مورد انتخاب شده
            </span>
          </template>

          <span
              v-else
              class="list-toolbar__title"
          >
            لیست درخواست‌ها
          </span>
        </div>

        <div class="list-toolbar__actions">
          <template v-if="deleteMode">
            <AppButton
                variant="secondary"
                size="sm"
                :disabled="deleting"
                @click="exitDeleteMode"
            >
              انصراف
            </AppButton>

            <AppButton
                variant="danger"
                size="sm"
                icon="close"
                :disabled="!selectedCount"
                :loading="deleting"
                @click="
                openDeleteModal(selectedIds)
              "
            >
              {{
                selectedCount
                    ? `حذف ${selectedCount} مورد`
                    : 'حذف'
              }}
            </AppButton>
          </template>

          <AppButton
              v-else
              variant="danger"
              size="sm"
              icon="close"
              @click="enterDeleteMode"
          >
            حذف
          </AppButton>
        </div>
      </div>

      <div
          v-if="loading"
          class="kyc-state"
      >
        <AppIcon
            name="loader"
            :size="28"
        />

        <strong>
          در حال بارگیری درخواست‌ها...
        </strong>

        <span>
          لطفاً کمی صبر کنید.
        </span>
      </div>

      <div
          v-else-if="!filteredApplications.length"
          class="kyc-state"
      >
        <AppIcon
            name="search"
            :size="28"
        />

        <strong>
          درخواستی پیدا نشد.
        </strong>

        <span>
          عبارت جستجو را تغییر دهید.
        </span>
      </div>

      <div
          v-else
          class="kyc-table-wrap"
      >
        <table class="kyc-table">
          <thead>
          <tr>
            <th
                v-if="deleteMode"
                class="checkbox-column"
                aria-hidden="true"
            />

            <th class="user-column">
              کاربر
            </th>

            <th>
              اطلاعات هویتی
            </th>

            <th>
              مدرک
            </th>

            <th>
              بانک
            </th>

            <th>
              وضعیت کلی
            </th>

            <th class="action-column">
  <span class="action-column__title">
    عملیات
  </span>
            </th>
          </tr>
          </thead>

          <tbody>
          <tr
              v-for="application in filteredApplications"
              :key="application.id"
              :class="{
                'is-selected':
                  isSelected(application.id),
              }"
          >
            <td
                v-if="deleteMode"
                class="checkbox-column"
            >
              <input
                  type="checkbox"
                  :checked="
                    isSelected(application.id)
                  "
                  @change="
                    toggleSelection(
                      application.id,
                    )
                  "
              />
            </td>

            <td class="user-column">
              <div class="user-cell">
                  <span class="user-avatar">
                    {{
                      getUserInitials(
                          application,
                      )
                    }}
                  </span>

                <div class="user-cell__content">
                  <strong>
                    {{
                      getUserName(
                          application,
                      )
                    }}
                  </strong>

                  <small dir="ltr">
                    {{
                      application.phoneNumber
                      || '—'
                    }}
                  </small>
                </div>
              </div>
            </td>

            <td>
              <StatusBadge
                  domain="kyc"
                  :status="
                    application.basicInfoStatus
                  "
              />
            </td>

            <td>
              <StatusBadge
                  domain="kyc"
                  :status="
                    application.identityStatus
                  "
              />
            </td>

            <td>
              <StatusBadge
                  domain="bank"
                  :status="
                    getBankStatus(application)
                  "
              />
            </td>

            <td>
              <StatusBadge
                  domain="kyc"
                  :status="
                    application.status
                  "
              />
            </td>

            <td class="action-column">
              <div class="row-actions">
                <AppButton
                    variant="secondary"
                    size="sm"
                    icon="chevronLeft"
                    :loading="
                      loadingDetail &&
                      selectedApplication?.id ===
                        application.id
                    "
                    @click="
                      openApplication(
                        application.id,
                      )
                    "
                >
                  بررسی
                </AppButton>
              </div>
            </td>
          </tr>
          </tbody>
        </table>
      </div>
    </AppCard>

    <AppCard
        v-if="selectedApplication"
        padding="lg"
        class="detail-card"
    >
      <KycApplicationDetailPage
          :application="selectedApplication"
          @close="closeDetail"
          @updated="refreshApplication"
      />
    </AppCard>

    <AppModal
        :model-value="deleteTargets.length > 0"
        title="حذف درخواست‌ها"
        :description="
        `آیا از حذف ${deleteTargets.length} درخواست انتخاب‌شده مطمئن هستید؟ این عملیات قابل بازگشت نیست.`
      "
        size="sm"
        @update:model-value="
        (value) =>
          !value && closeDeleteModal()
      "
    >
      <div class="delete-confirm">
        <div class="delete-confirm__icon">
          <AppIcon
              name="warning"
              :size="24"
          />
        </div>

        <div class="delete-confirm__content">
          <strong>
            حذف
            {{ deleteTargets.length }}
            درخواست
          </strong>

          <p>
            اطلاعات درخواست‌های انتخاب‌شده از
            سیستم حذف خواهند شد.
          </p>
        </div>

        <div class="delete-confirm__actions">
          <AppButton
              variant="secondary"
              :disabled="deleting"
              @click="closeDeleteModal"
          >
            انصراف
          </AppButton>

          <AppButton
              variant="danger"
              :loading="deleting"
              @click="confirmDelete"
          >
            حذف نهایی
          </AppButton>
        </div>
      </div>
    </AppModal>
  </div>
</template>

<style scoped>
.kyc-page {
  display: grid;
  gap: .85rem;
}

.kyc-toolbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1.5rem;
  margin-bottom: -.25rem;
}

.kyc-toolbar__copy {
  min-width: 0;
}

.kyc-toolbar__actions {
  display: flex;
  align-items: flex-end;
  flex: 0 0 auto;
  gap: .65rem;
}

.eyebrow {
  display: inline-flex;
  margin-bottom: .4rem;
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  font-weight: 800;
}

.kyc-toolbar h2 {
  margin: 0;
  color: var(--color-text-primary);
  font-size: clamp(1.35rem, 2vw, 1.7rem);
  line-height: 1.3;
}

.kyc-toolbar p {
  max-width: 46rem;
  margin: .35rem 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  line-height: 1.7;
}

.toolbar-search {
  position: relative;
  width: 22rem;
}

.toolbar-search {
  position: relative;
  width: 22rem;
}

.toolbar-search :deep(input) {
  padding-left: 3rem !important;
}

.toolbar-search__clear {
  position: absolute;
  left: .7rem;
  bottom: .72rem;
  z-index: 2;

  display: grid;
  width: 1.7rem;
  height: 1.7rem;
  padding: 0;
  border: 0;
  border-radius: .5rem;
  background: var(--color-surface-2);
  color: var(--color-text-muted);
  place-items: center;
  cursor: pointer;
  transition: background var(--transition-fast),
  color var(--transition-fast);
}

.toolbar-search__clear:hover {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}


.overview-grid {
  display: grid;
  grid-template-columns: repeat(
    4,
    minmax(0, 1fr)
  );
  gap: .75rem;
}

.overview-card {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: 5rem;
  padding: .9rem 1rem;
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.overview-card__icon {
  display: grid;
  width: 2.55rem;
  height: 2.55rem;
  flex: 0 0 auto;
  border-radius: .75rem;
  place-items: center;
}

.overview-card__icon.primary {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.overview-card__icon.warning {
  background: var(--color-warning-soft);
  color: var(--color-warning);
}

.overview-card__icon.success {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.overview-card__icon.danger {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.overview-card > div:last-child {
  display: grid;
  gap: .15rem;
}

.overview-card span {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.overview-card strong {
  color: var(--color-text-primary);
  font-size: 1.15rem;
}

.page-notice {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: .8rem 1rem;
  border: 1px solid;
  border-radius: var(--radius-md);
}

.page-notice span {
  flex: 1;
}

.page-notice.danger {
  border-color: rgba(
      240,
      108,
      117,
      .24
  );
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.kyc-list-card {
  overflow: hidden;
}

.list-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  min-height: 4rem;
  padding: .75rem 1rem;
  border-bottom: 1px solid var(--color-border-soft);
  background: var(--color-surface);
}

.list-toolbar__left,
.list-toolbar__actions {
  display: flex;
  align-items: center;
  gap: .7rem;
}

.list-toolbar__title {
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.select-all {
  display: inline-flex;
  align-items: center;
  gap: .5rem;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  user-select: none;
}

.selected-count {
  padding: .3rem .65rem;
  border-radius: 999px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  font-weight: 700;
}

.kyc-table-wrap {
  overflow-x: auto;
}

.kyc-table {
  width: 100%;
  min-width: 900px;
  border-collapse: separate;
  border-spacing: 0;
}

.kyc-table th,
.kyc-table td {
  padding: .9rem 1rem;
  border-bottom: 1px solid var(--color-border-soft);
  text-align: right;
  vertical-align: middle;
}

.kyc-table th {
  background: var(--color-surface-2);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-weight: 800;
  white-space: nowrap;
}

.kyc-table td {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  background: var(--color-surface);
}

.kyc-table tbody tr {
  transition: background var(--transition-fast),
  box-shadow var(--transition-fast);
}

.kyc-table tbody tr:hover td {
  background: var(--color-surface-2);
}

.kyc-table tbody tr.is-selected td {
  background: var(--color-primary-soft);
}

.kyc-table tbody tr:last-child td {
  border-bottom: 0;
}

.checkbox-column {
  width: 3.25rem;
  min-width: 3.25rem;
  max-width: 3.25rem;
  padding-inline: .7rem !important;
  text-align: center !important;
}

.user-column {
  min-width: 235px;
}

.action-column {
  width: 9rem;
  min-width: 9rem;
  text-align: left !important;
  padding-left: 1rem !important;
  padding-right: 1rem !important;
}

.kyc-table input[type='checkbox'],
.select-all input[type='checkbox'] {
  width: 1rem;
  height: 1rem;
  margin: 0;
  accent-color: var(--color-primary);
  cursor: pointer;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: .7rem;
  min-width: 0;
}

.user-avatar {
  display: grid;
  width: 2.5rem;
  height: 2.5rem;
  flex: 0 0 auto;
  border: 1px solid var(--color-border-soft);
  border-radius: .75rem;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: .78rem;
  font-weight: 800;
  place-items: center;
}

.user-cell__content {
  display: grid;
  gap: .2rem;
  min-width: 0;
}

.user-cell__content strong {
  overflow: hidden;
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-cell__content small {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.row-actions {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.row-actions :deep(.app-button) {
  width: 5rem;
  min-width: 5rem;
  white-space: nowrap;
}

.action-column__title {
  display: inline-flex;
  width: 5rem;
  justify-content: center;
  white-space: nowrap;
  transform: translateX(30px);
}

.kyc-state {
  display: grid;
  min-height: 17rem;
  padding: 2rem;
  align-content: center;
  justify-items: center;
  gap: .5rem;
  color: var(--color-text-muted);
  text-align: center;
}

.kyc-state strong {
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}

.kyc-state span {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.detail-card {
  scroll-margin-top: var(--space-5);
}

.delete-confirm {
  display: grid;
  gap: var(--space-4);
}

.delete-confirm__icon {
  display: grid;
  width: 3rem;
  height: 3rem;
  border-radius: .9rem;
  background: var(--color-danger-soft);
  color: var(--color-danger);
  place-items: center;
}

.delete-confirm__content {
  display: grid;
  gap: .35rem;
}

.delete-confirm__content strong {
  color: var(--color-text-primary);
}

.delete-confirm__content p {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  line-height: 1.8;
}

.delete-confirm__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  padding-top: var(--space-2);
}

@media (max-width: 900px) {
  .kyc-toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .kyc-toolbar__actions {
    align-items: stretch;
    width: 100%;
  }

  .toolbar-search {
    width: 100%;
  }

  .overview-grid {
    grid-template-columns: repeat(
      2,
      minmax(0, 1fr)
    );
  }
}

@media (max-width: 760px) {
  .list-toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .list-toolbar__left,
  .list-toolbar__actions {
    width: 100%;
  }

  .list-toolbar__actions {
    justify-content: flex-end;
  }
}

@media (max-width: 560px) {
  .overview-grid {
    grid-template-columns: 1fr;
  }

  .delete-confirm__actions {
    flex-direction: column;
  }
}
</style>