<script setup lang="ts">
import {computed, defineAsyncComponent, onBeforeUnmount, onMounted, reactive, ref, watch,} from 'vue'

import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppSwitch from '@/components/ui/AppSwitch.vue'
import CopyButton from '@/components/ui/CopyButton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import QrCode from '@/components/wallet/QrCode.vue'
import AssetSelect from '@/components/finance/AssetSelect.vue'
import NetworkSelector from '@/components/wallet/NetworkSelector.vue'
import OtpInput from '@/components/ui/OtpInput.vue'
import {assetService} from '@/services/asset.service'
import {ApiError, securityService, walletService, withdrawalAddressService,} from '@/services'

import type {
  ActiveSession,
  AssetNetwork,
  SecurityEvent,
  SecurityOverview,
  TwoFactorSetup,
  WalletAsset,
  WithdrawalAddress,
  WithdrawalAddressConfirmation,
} from '@/types'

import {formatPersianDateTime, formatRelativeTime, normalizeDigits, toPersianDigits,} from '@/utils/formatters'

const DemoCodeHint =
    import.meta.env.DEV &&
    import.meta.env.VITE_USE_MOCK_API === 'true'
        ? defineAsyncComponent(
            () => import('@/components/ui/DemoCodeHint.vue'),
        )
        : null

type ConfirmationAction =
    | {
  kind: 'session'
  session: ActiveSession
}
    | {
  kind: 'other-sessions'
}
    | {
  kind: 'disable-2fa'
}
    | {
  kind: 'whitelist'
  enabled: boolean
}

type PhishingMode = 'create' | 'existing'

const overview = ref<SecurityOverview | null>(null)
const sessions = ref<ActiveSession[]>([])
const events = ref<SecurityEvent[]>([])

const loading = ref(true)
const error = ref('')
const feedback = ref('')

const confirmation = ref<ConfirmationAction | null>(null)
const confirming = ref(false)

const passwordOpen = ref(false)
const changingPassword = ref(false)
const passwordError = ref('')
const passwordFields = reactive<Record<string, string>>({})

const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  newPasswordConfirmation: '',
})

const twoFactorOpen = ref(false)
const twoFactorCode = ref('')
const twoFactorError = ref('')
const twoFactorLoading = ref(false)
const twoFactorSetup =
    ref<TwoFactorSetup | null>(null)

const disableTwoFactorCode = ref('')
const disableTwoFactorError = ref('')

watch(twoFactorOpen, (open) => {
  if (open || twoFactorLoading.value) return

  twoFactorSetup.value = null
  twoFactorCode.value = ''
  twoFactorError.value = ''
})

const phishingOpen = ref(false)
const phishingCode = ref('')
const phishingError = ref('')
const phishingLoading = ref(false)
const phishingMode =
    ref<PhishingMode>('create')

const withdrawalAddresses =
    ref<WithdrawalAddress[]>([])

const withdrawalAddressesLoading =
    ref(false)

const withdrawalAddressActionLoading =
    ref('')

const withdrawalAddressModalOpen =
    ref(false)

const withdrawalAddressDetailsOpen =
    ref(false)

const withdrawalAddressDetailsId =
    ref('')

const withdrawalAddressConfirmationOpen =
    ref(false)

const withdrawalAddressCreating =
    ref(false)

const withdrawalAddressConfirming =
    ref(false)

const withdrawalAddressResending =
    ref(false)

const withdrawalAddressConfirmation =
    ref<WithdrawalAddressConfirmation | null>(null)

const withdrawalAddressAsset =
    ref('')

const withdrawalAddressNetwork =
    ref('')

const withdrawalAddressValue =
    ref('')

const withdrawalAddressMemo =
    ref('')

const withdrawalAddressLabel =
    ref('')

const withdrawalAddressError =
    ref('')

const withdrawalAddressMemoError =
    ref('')

const withdrawalAddressLabelError =
    ref('')

const withdrawalAddressCreateError =
    ref('')

const withdrawalAddressOtp =
    ref('')

const withdrawalAddressTwoFactorCode =
    ref('')

const withdrawalAddressOtpError =
    ref('')

const withdrawalAddressTwoFactorError =
    ref('')

const withdrawalAddressSecurityMessage =
    ref('')

const withdrawalAddressExpiresAt =
    ref('')

const withdrawalAddressResendAt =
    ref('')

const pendingWithdrawalAddressId =
    ref('')

const pendingWithdrawalAddressPreview =
    ref('')

const walletAssets =
    ref<WalletAsset[]>([])

const withdrawalAssets =
    ref<Awaited<ReturnType<typeof assetService.list>>>([])

const withdrawalNetworks =
    ref<AssetNetwork[]>([])

const withdrawalNetworkLoading =
    ref(false)

const withdrawalAddressNowMs =
    ref(Date.now())

let withdrawalAddressClockTimer:
    number | undefined

const withdrawalAddressConfirmationExpired =
    computed(() =>
        !withdrawalAddressExpiresAt.value ||
        Date.parse(
            withdrawalAddressExpiresAt.value,
        ) <= withdrawalAddressNowMs.value,
    )

const withdrawalAddressConfirmationSecondsRemaining =
    computed(() =>
        withdrawalAddressExpiresAt.value
            ? Math.max(
                0,
                Math.ceil(
                    (
                        Date.parse(
                            withdrawalAddressExpiresAt.value,
                        ) -
                        withdrawalAddressNowMs.value
                    ) / 1000,
                ),
            )
            : 0,
    )

const withdrawalAddressResendDelay =
    computed(() =>
        withdrawalAddressResendAt.value
            ? Math.max(
                0,
                Math.ceil(
                    (
                        Date.parse(
                            withdrawalAddressResendAt.value,
                        ) -
                        withdrawalAddressNowMs.value
                    ) / 1000,
                ),
            )
            : 0,
    )

const visibleWithdrawalAddresses =
    computed(() =>
        withdrawalAddresses.value.filter(
            (item) =>
                item.status !== 'revoked',
        ),
    )

const cryptoWalletAssets =
    computed(() =>
        withdrawalAssets.value.filter(
            (asset) => asset.symbol !== 'IRT',
        ),
    )

const withdrawalAssetBalances =
    computed<Record<string, string>>(() =>
        Object.fromEntries(
            walletAssets.value
                .filter(
                    (asset) => asset.symbol !== 'IRT',
                )
                .map(
                    (asset) => [
                      asset.symbol,
                      asset.available,
                    ],
                ),
        ),
    )

const disabledWithdrawalAssetSymbols =
    computed(() =>
        cryptoWalletAssets.value
            .filter(
                (asset) =>
                    !asset.withdrawalEnabled,
            )
            .map(
                (asset) =>
                    asset.symbol,
            ),
    )

const disabledWithdrawalAssetDescriptions =
    computed<Record<string, string>>(() =>
        Object.fromEntries(
            disabledWithdrawalAssetSymbols.value.map(
                (symbol) => [
                  symbol,
                  'برداشت این ارز موقتاً غیرفعال است',
                ],
            ),
        ),
    )

const selectedWithdrawalAsset =
    computed(() =>
        cryptoWalletAssets.value.find(
            (asset) =>
                asset.symbol ===
                withdrawalAddressAsset.value,
        ),
    )

const selectedWithdrawalNetwork =
    computed(() =>
        withdrawalNetworks.value.find(
            (network) =>
                network.code ===
                withdrawalAddressNetwork.value,
        ),
    )

const selectedWithdrawalAddress =
    computed(() =>
        visibleWithdrawalAddresses.value.find(
            (address) =>
                String(address.id) ===
                withdrawalAddressDetailsId.value,
        ),
    )

const otherSessionCount = computed(() =>
    sessions.value.filter(
        (session) => !session.current,
    ).length,
)

const scoreTone = computed(() => {
  const score =
      overview.value?.score ?? 0

  return score >= 85
      ? 'strong'
      : score >= 65
          ? 'medium'
          : 'weak'
})

const scoreLabel = computed(() =>
    scoreTone.value === 'strong'
        ? 'امنیت عالی'
        : scoreTone.value === 'medium'
            ? 'امنیت خوب'
            : 'نیازمند توجه',
)

const confirmationCopy = computed(() => {
  const action =
      confirmation.value

  if (!action) {
    return {
      title: '',
      description: '',
      confirm: '',
    }
  }

  if (action.kind === 'session') {
    return {
      title: 'قطع دسترسی این دستگاه؟',
      description:
          `دسترسی ${action.session.deviceName} فوراً قطع می‌شود و این نشست دیگر معتبر نخواهد بود.`,
      confirm: 'قطع دسترسی',
    }
  }

  if (action.kind === 'other-sessions') {
    return {
      title: 'خروج از سایر دستگاه‌ها؟',
      description:
          `${toPersianDigits(otherSessionCount.value)} نشست دیگر پایان می‌یابد و فقط همین دستگاه متصل می‌ماند.`,
      confirm: 'خروج از همه',
    }
  }

  if (action.kind === 'disable-2fa') {
    return {
      title:
          'غیرفعال‌کردن ورود دومرحله‌ای؟',
      description:
          'با غیرفعال‌کردن این لایه، امنیت ورود حساب کمتر می‌شود.',
      confirm: 'غیرفعال شود',
    }
  }

  return {
    title: action.enabled
        ? 'فعال‌کردن فهرست مجاز برداشت؟'
        : 'غیرفعال‌کردن فهرست مجاز؟',
    description: action.enabled
        ? 'پس از فعال‌سازی، برداشت فقط به آدرس‌های تأییدشده انجام می‌شود.'
        : 'پس از غیرفعال‌سازی، محدودیت فهرست مجاز روی برداشت اعمال نمی‌شود.',
    confirm: action.enabled
        ? 'فعال شود'
        : 'غیرفعال شود',
  }
})

function readableError(
    caught: unknown,
    fallback: string,
): string {
  return caught instanceof Error
      ? caught.message
      : fallback
}

function formatSecurityEventTime(
    value: string,
): string {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return '—'
  }

  const now = new Date()

  const today = new Date(
      now.getFullYear(),
      now.getMonth(),
      now.getDate(),
  )

  const eventDay = new Date(
      date.getFullYear(),
      date.getMonth(),
      date.getDate(),
  )

  const diffDays = Math.floor(
      (
          today.getTime() -
          eventDay.getTime()
      ) /
      (24 * 60 * 60 * 1000),
  )

  if (diffDays === 0) {
    return formatRelativeTime(value)
  }

  if (diffDays === 1) {
    return 'دیروز'
  }

  if (diffDays >= 2) {
    return `${toPersianDigits(diffDays)} روز پیش`
  }

  return formatRelativeTime(value)
}

function deviceIcon(
    type: ActiveSession['deviceType'],
): string {
  return type === 'mobile'
      ? 'phone'
      : type === 'tablet'
          ? 'dashboard'
          : 'markets'
}

function eventIcon(
    type: string,
): string {
  const icons: Record<string, string> = {
    otp_requested: 'shield',
    otp_verified: 'shield',
    otp_failed: 'warning',

    login_success: 'shield',
    login_failure: 'warning',

    registration_success: 'check',
    logout: 'logout',

    password_change: 'lock',
    password_reset_success: 'lock',

    kyc_update: 'verify',
    security_alert: 'warning',

    two_factor_enabled: 'shield',
    two_factor_disabled: 'shield',

    anti_phishing_created: 'mail',
    anti_phishing_updated: 'mail',
    anti_phishing_deleted: 'mail',

    session_revoked: 'logout',

    withdrawal_confirmed: 'wallet',

    withdrawal_addr_confirm_req:
        'shield',
    withdrawal_addr_confirmed:
        'check',
    withdrawal_addr_activated:
        'wallet',
    withdrawal_addr_revoked:
        'warning',
    withdrawal_addr_default:
        'wallet',

    withdrawal_whitelist_enabled:
        'check',
    withdrawal_whitelist_disabled:
        'warning',
  }

  return icons[type] ?? 'clock'
}

function eventTone(
    type: string,
): string {
  if (
      type === 'login_failure' ||
      type === 'otp_failed' ||
      type ===
      'withdrawal_addr_revoked' ||
      type ===
      'withdrawal_whitelist_disabled'
  ) {
    return 'danger'
  }

  if (
      type === 'two_factor_disabled' ||
      type === 'anti_phishing_deleted' ||
      type === 'logout'
  ) {
    return 'warning'
  }

  if (
      type === 'two_factor_enabled' ||
      type === 'password_change' ||
      type ===
      'password_reset_success' ||
      type ===
      'anti_phishing_created' ||
      type ===
      'anti_phishing_updated' ||
      type ===
      'registration_success' ||
      type ===
      'withdrawal_addr_confirmed' ||
      type ===
      'withdrawal_addr_activated' ||
      type ===
      'withdrawal_addr_default' ||
      type ===
      'withdrawal_whitelist_enabled'
  ) {
    return 'success'
  }

  return 'info'
}

function withdrawalAddressStatusLabel(
    status: WithdrawalAddress['status'],
): string {
  switch (status) {
    case 'active':
      return 'فعال'

    case 'pending_confirmation':
      return 'در انتظار تأیید'

    case 'cooling_down':
      return 'دوره امنیتی'

    case 'disabled':
      return 'غیرفعال'

    case 'blocked':
      return 'مسدود'

    case 'revoked':
      return 'لغوشده'

    default:
      return 'نامشخص'
  }
}

function withdrawalAddressStatusTone(
    status: WithdrawalAddress['status'],
): string {
  switch (status) {
    case 'active':
      return 'success'

    case 'pending_confirmation':
    case 'cooling_down':
      return 'warning'

    case 'blocked':
    case 'revoked':
    case 'disabled':
      return 'danger'

    default:
      return 'info'
  }
}

function cooldownSecondsRemaining(
    address: WithdrawalAddress,
): number {
  if (
      address.status !==
      'cooling_down' ||
      !address.cooldownUntil
  ) {
    return 0
  }

  return Math.max(
      0,
      Math.ceil(
          (
              Date.parse(
                  address.cooldownUntil,
              ) -
              withdrawalAddressNowMs.value
          ) / 1000,
      ),
  )
}

function formatCooldownRemaining(
    seconds: number,
): string {
  const remaining =
      Math.max(0, Math.floor(seconds))

  if (remaining < 60) {
    return `${toPersianDigits(remaining)} ثانیه`
  }

  const minutes =
      Math.floor(remaining / 60)

  const hours =
      Math.floor(minutes / 60)

  const days =
      Math.floor(hours / 24)

  const remainingHours =
      hours % 24

  const remainingMinutes =
      minutes % 60

  if (days > 0) {
    if (remainingHours > 0) {
      return `${toPersianDigits(days)} روز و ${toPersianDigits(remainingHours)} ساعت`
    }

    return `${toPersianDigits(days)} روز`
  }

  if (hours > 0) {
    if (remainingMinutes > 0) {
      return `${toPersianDigits(hours)} ساعت و ${toPersianDigits(remainingMinutes)} دقیقه`
    }

    return `${toPersianDigits(hours)} ساعت`
  }

  return `${toPersianDigits(remainingMinutes)} دقیقه`
}

function resetWithdrawalAddressForm(): void {
  withdrawalAddressAsset.value = ''
  withdrawalAddressNetwork.value = ''
  withdrawalAddressValue.value = ''
  withdrawalAddressMemo.value = ''
  withdrawalAddressLabel.value = ''

  withdrawalAddressError.value = ''
  withdrawalAddressMemoError.value = ''
  withdrawalAddressLabelError.value = ''
  withdrawalAddressCreateError.value = ''

  withdrawalNetworks.value = []
}

async function loadWithdrawalAddresses(): Promise<void> {
  withdrawalAddressesLoading.value = true
  withdrawalAddressCreateError.value = ''

  try {
    withdrawalAddresses.value =
        await withdrawalAddressService.list()
  } catch (caught) {
    withdrawalAddressCreateError.value =
        readableError(
            caught,
            'فهرست آدرس‌های برداشت دریافت نشد.',
        )
  } finally {
    withdrawalAddressesLoading.value = false
  }
}

async function loadWithdrawalAssets(): Promise<void> {
  try {
    const assets =
        await assetService.list()

    withdrawalAssets.value =
        assets
  } catch {
    withdrawalAssets.value = []
  }

  try {
    const wallet =
        await walletService.getSummary()

    walletAssets.value =
        wallet.assets
  } catch {
    walletAssets.value = []
  }
}

async function loadWithdrawalNetworks(
    symbol: string,
): Promise<void> {
  withdrawalNetworks.value = []
  withdrawalAddressNetwork.value = ''

  withdrawalAddressValue.value = ''
  withdrawalAddressMemo.value = ''

  withdrawalAddressError.value = ''
  withdrawalAddressMemoError.value = ''

  if (!symbol) {
    return
  }

  withdrawalNetworkLoading.value =
      true

  try {
    const networks =
        await assetService.getNetworks(
            symbol as WalletAsset['symbol'],
        )

    withdrawalNetworks.value =
        networks.filter(
            (network) =>
                network.withdrawalEnabled &&
                network.status !== 'disabled' &&
                network.status !== 'maintenance',
        )

    withdrawalAddressNetwork.value =
        withdrawalNetworks.value.find(
            (network) =>
                network.status === 'active',
        )?.code || ''
  } catch (caught) {
    withdrawalAddressCreateError.value =
        readableError(
            caught,
            'شبکه‌های این ارز دریافت نشدند.',
        )
  } finally {
    withdrawalNetworkLoading.value =
        false
  }
}

function openWithdrawalAddressModal(): void {
  resetWithdrawalAddressForm()
  withdrawalAddressModalOpen.value =
      true
}

function openWithdrawalAddressDetails(
    address: WithdrawalAddress,
): void {
  withdrawalAddressDetailsId.value =
      String(address.id)
  withdrawalAddressDetailsOpen.value =
      true
}

function closeWithdrawalAddressDetails(): void {
  if (withdrawalAddressActionLoading.value) {
    return
  }

  withdrawalAddressDetailsOpen.value =
      false
  withdrawalAddressDetailsId.value =
      ''
}

async function setSelectedWithdrawalAddressDefault(): Promise<void> {
  const address =
      selectedWithdrawalAddress.value

  if (
      !address ||
      address.status !== 'active' ||
      address.isDefault
  ) {
    return
  }

  await setWithdrawalAddressDefault(
      address,
  )
}

function closeWithdrawalAddressModal(): void {
  if (
      withdrawalAddressCreating.value
  ) {
    return
  }

  withdrawalAddressModalOpen.value =
      false
}

function validateWithdrawalAddressForm(): boolean {
  withdrawalAddressError.value = ''
  withdrawalAddressMemoError.value = ''
  withdrawalAddressLabelError.value =
      ''
  withdrawalAddressCreateError.value =
      ''

  if (
      !overview.value?.mobileVerified
  ) {
    withdrawalAddressCreateError.value =
        'برای افزودن آدرس برداشت ابتدا شماره موبایل خود را تأیید کنید.'
    return false
  }

  if (!withdrawalAddressAsset.value) {
    withdrawalAddressCreateError.value =
        'ارز را انتخاب کنید.'
    return false
  }

  if (!withdrawalAddressNetwork.value) {
    withdrawalAddressCreateError.value =
        'شبکه را انتخاب کنید.'
    return false
  }

  const network =
      selectedWithdrawalNetwork.value

  if (!network) {
    withdrawalAddressCreateError.value =
        'شبکه انتخاب‌شده معتبر نیست.'
    return false
  }

  const address =
      withdrawalAddressValue.value.trim()

  if (!address) {
    withdrawalAddressError.value =
        'آدرس برداشت را وارد کنید.'
    return false
  }

  if (/\s/.test(address)) {
    withdrawalAddressError.value =
        'آدرس برداشت نباید فاصله داشته باشد.'
    return false
  }

  if (network.addressRegex) {
    try {
      if (
          !new RegExp(
              network.addressRegex,
          ).test(address)
      ) {
        withdrawalAddressError.value =
            `ساختار آدرس با شبکه ${network.code} هم‌خوانی ندارد.`
        return false
      }
    } catch {
      return false
    }
  } else if (address.length < 12) {
    withdrawalAddressError.value =
        'طول آدرس معتبر نیست.'
    return false
  }

  if (
      network.memoRequired &&
      !withdrawalAddressMemo.value.trim()
  ) {
    withdrawalAddressMemoError.value =
        'ممو یا تگ این شبکه الزامی است.'
    return false
  }

  return true
}

async function createWithdrawalAddress(): Promise<void> {
  if (
      withdrawalAddressCreating.value
  ) {
    return
  }

  if (!validateWithdrawalAddressForm()) {
    return
  }

  withdrawalAddressCreating.value =
      true
  withdrawalAddressCreateError.value =
      ''

  try {
    const response =
        await withdrawalAddressService.create(
            {
              asset:
              withdrawalAddressAsset.value,
              network:
              withdrawalAddressNetwork.value,
              address:
                  withdrawalAddressValue.value.trim(),
              memo:
                  withdrawalAddressMemo.value.trim() ||
                  undefined,
              label:
                  withdrawalAddressLabel.value.trim() ||
                  undefined,
            },
        )

    withdrawalAddresses.value = [
      response.address,
      ...withdrawalAddresses.value.filter(
          (item) =>
              String(item.id) !==
              String(response.address.id),
      ),
    ]

    pendingWithdrawalAddressId.value =
        String(response.address.id)

    pendingWithdrawalAddressPreview.value =
        response.address.address

    withdrawalAddressConfirmation.value =
        response.confirmation

    withdrawalAddressOtp.value = ''
    withdrawalAddressTwoFactorCode.value =
        ''
    withdrawalAddressOtpError.value = ''
    withdrawalAddressTwoFactorError.value =
        ''
    withdrawalAddressSecurityMessage.value =
        ''

    withdrawalAddressExpiresAt.value =
        new Date(
            Date.now() +
            response.confirmation.expiresIn *
            1_000,
        ).toISOString()

    withdrawalAddressResendAt.value =
        new Date(
            Date.now() +
            response.confirmation.resendAvailableIn *
            1_000,
        ).toISOString()

    withdrawalAddressModalOpen.value =
        false
    withdrawalAddressConfirmationOpen.value =
        true

    withdrawalAddressNowMs.value =
        Date.now()
  } catch (caught) {
    if (caught instanceof ApiError) {
      withdrawalAddressError.value =
          caught.details?.fields?.address ||
          ''

      withdrawalAddressMemoError.value =
          caught.details?.fields?.memo ||
          ''

      withdrawalAddressLabelError.value =
          caught.details?.fields?.label ||
          ''
    }

    withdrawalAddressCreateError.value =
        readableError(
            caught,
            'ثبت آدرس برداشت انجام نشد.',
        )
  } finally {
    withdrawalAddressCreating.value =
        false
  }
}

async function confirmWithdrawalAddress(): Promise<void> {
  if (
      withdrawalAddressConfirming.value ||
      !pendingWithdrawalAddressId.value ||
      !withdrawalAddressConfirmation.value
  ) {
    return
  }

  withdrawalAddressOtpError.value = ''
  withdrawalAddressTwoFactorError.value =
      ''

  const otp =
      normalizeDigits(
          withdrawalAddressOtp.value,
      )
          .replace(/\D/g, '')
          .slice(0, 6)

  if (otp.length !== 6) {
    withdrawalAddressOtpError.value =
        'کد تأیید شش‌رقمی را کامل وارد کنید.'
    return
  }

  const twoFactorCode =
      normalizeDigits(
          withdrawalAddressTwoFactorCode.value,
      )
          .replace(/\D/g, '')
          .slice(0, 6)

  if (
      overview.value?.twoFactorEnabled &&
      twoFactorCode.length !== 6
  ) {
    withdrawalAddressTwoFactorError.value =
        'کد Authenticator را کامل وارد کنید.'
    return
  }

  if (
      withdrawalAddressConfirmationExpired.value
  ) {
    withdrawalAddressOtpError.value =
        'مهلت کد تأیید تمام شده است.'
    return
  }

  withdrawalAddressConfirming.value =
      true

  try {
    const confirmed =
        await withdrawalAddressService.confirm(
            pendingWithdrawalAddressId.value,
            {
              challengeId:
              withdrawalAddressConfirmation.value
                  .challengeId,
              otp,
              twoFactorCode:
                  overview.value?.twoFactorEnabled
                      ? twoFactorCode
                      : undefined,
            },
        )

    withdrawalAddresses.value = [
      confirmed,
      ...withdrawalAddresses.value.filter(
          (item) =>
              String(item.id) !==
              String(confirmed.id),
      ),
    ]

    withdrawalAddressConfirmationOpen.value =
        false

    withdrawalAddressOtp.value = ''
    withdrawalAddressTwoFactorCode.value =
        ''

    pendingWithdrawalAddressId.value = ''
    pendingWithdrawalAddressPreview.value =
        ''

    withdrawalAddressConfirmation.value =
        null
    withdrawalAddressExpiresAt.value = ''
    withdrawalAddressResendAt.value = ''

    withdrawalAddressSecurityMessage.value =
        confirmed.status === 'active'
            ? 'آدرس برداشت با موفقیت فعال شد.'
            : 'آدرس برداشت تأیید شد و وارد دوره امنیتی شد.'

    feedback.value =
        withdrawalAddressSecurityMessage.value

    await loadWithdrawalAddresses()

    events.value =
        await securityService.listEvents()
  } catch (caught) {
    if (caught instanceof ApiError) {
      withdrawalAddressOtpError.value =
          caught.details?.fields?.otp || ''

      withdrawalAddressTwoFactorError.value =
          caught.details?.fields
              ?.twoFactorCode || ''
    }

    if (
        !withdrawalAddressOtpError.value &&
        !withdrawalAddressTwoFactorError.value
    ) {
      withdrawalAddressOtpError.value =
          readableError(
              caught,
              'تأیید آدرس انجام نشد.',
          )
    }
  } finally {
    withdrawalAddressConfirming.value =
        false
  }
}

async function resendWithdrawalAddressConfirmation(): Promise<void> {
  if (
      withdrawalAddressResending.value ||
      !pendingWithdrawalAddressId.value
  ) {
    return
  }

  if (
      withdrawalAddressResendDelay.value > 0
  ) {
    return
  }

  withdrawalAddressResending.value =
      true
  withdrawalAddressOtpError.value = ''
  withdrawalAddressSecurityMessage.value =
      ''

  try {
    const response =
        await withdrawalAddressService
            .resendConfirmation(
                pendingWithdrawalAddressId.value,
            )

    withdrawalAddresses.value = [
      response.address,
      ...withdrawalAddresses.value.filter(
          (item) =>
              String(item.id) !==
              String(response.address.id),
      ),
    ]

    withdrawalAddressConfirmation.value =
        response.confirmation

    withdrawalAddressExpiresAt.value =
        new Date(
            Date.now() +
            response.confirmation.expiresIn *
            1_000,
        ).toISOString()

    withdrawalAddressResendAt.value =
        new Date(
            Date.now() +
            response.confirmation.resendAvailableIn *
            1_000,
        ).toISOString()

    withdrawalAddressOtp.value = ''
    withdrawalAddressNowMs.value =
        Date.now()

    withdrawalAddressSecurityMessage.value =
        'کد تأیید دوباره ارسال شد.'
  } catch (caught) {
    withdrawalAddressOtpError.value =
        readableError(
            caught,
            'ارسال دوباره کد انجام نشد.',
        )
  } finally {
    withdrawalAddressResending.value =
        false
  }
}

async function setWithdrawalAddressDefault(
    address: WithdrawalAddress,
): Promise<void> {
  if (
      withdrawalAddressActionLoading.value
  ) {
    return
  }

  if (address.status !== 'active') {
    return
  }

  withdrawalAddressActionLoading.value =
      `default:${address.id}`

  try {
    const updated =
        await withdrawalAddressService.setDefault(
            String(address.id),
        )

    withdrawalAddresses.value =
        withdrawalAddresses.value.map(
            (item) => ({
              ...item,
              isDefault:
                  String(item.id) ===
                  String(updated.id),
            }),
        )

    feedback.value =
        'آدرس پیش‌فرض برداشت تغییر کرد.'

    events.value =
        await securityService.listEvents()
  } catch (caught) {
    error.value =
        readableError(
            caught,
            'تغییر آدرس پیش‌فرض انجام نشد.',
        )
  } finally {
    withdrawalAddressActionLoading.value =
        ''
  }
}

async function load(): Promise<void> {
  loading.value = true
  error.value = ''

  try {
    const [
      securityOverview,
      activeSessions,
      securityEvents,
    ] = await Promise.all([
      securityService.getOverview(),
      securityService.listSessions(),
      securityService.listEvents(),
    ])

    await Promise.all([
      loadWithdrawalAssets(),
      loadWithdrawalAddresses(),
    ])

    overview.value =
        securityOverview

    sessions.value =
        activeSessions

    events.value =
        securityEvents
  } catch (caught) {
    error.value =
        readableError(
            caught,
            'اطلاعات امنیتی بارگیری نشد.',
        )
  } finally {
    loading.value = false
  }
}

function resetPasswordForm(): void {
  passwordForm.currentPassword = ''
  passwordForm.newPassword = ''
  passwordForm.newPasswordConfirmation =
      ''

  passwordError.value = ''

  Object.keys(passwordFields).forEach(
      (key) =>
          delete passwordFields[key],
  )
}

function openPassword(): void {
  resetPasswordForm()
  passwordOpen.value = true
}

function validatePassword(): boolean {
  Object.keys(passwordFields).forEach(
      (key) =>
          delete passwordFields[key],
  )

  if (
      passwordForm.currentPassword.length <
      8
  ) {
    passwordFields.currentPassword =
        'رمز عبور فعلی را کامل وارد کنید.'
  }

  if (
      passwordForm.newPassword.length < 8
  ) {
    passwordFields.newPassword =
        'رمز جدید باید حداقل ۸ کاراکتر باشد.'
  }

  if (
      passwordForm.newPassword !==
      passwordForm.newPasswordConfirmation
  ) {
    passwordFields.newPasswordConfirmation =
        'تکرار رمز با رمز جدید یکسان نیست.'
  }

  if (
      passwordForm.currentPassword ===
      passwordForm.newPassword
  ) {
    passwordFields.newPassword =
        'رمز جدید باید با رمز فعلی متفاوت باشد.'
  }

  return (
      Object.keys(passwordFields).length === 0
  )
}

async function changePassword(): Promise<void> {
  if (!validatePassword()) return

  changingPassword.value = true
  passwordError.value = ''

  try {
    await securityService.changePassword(
        passwordForm,
    )

    passwordOpen.value = false
    resetPasswordForm()

    feedback.value =
        'رمز عبور با موفقیت تغییر کرد.'

    events.value =
        await securityService.listEvents()
  } catch (caught) {
    if (
        caught instanceof ApiError &&
        caught.details?.fields
    ) {
      Object.assign(
          passwordFields,
          caught.details.fields,
      )
    }

    passwordError.value =
        readableError(
            caught,
            'تغییر رمز عبور انجام نشد.',
        )
  } finally {
    changingPassword.value = false
  }
}

async function requestTwoFactorChange(): Promise<void> {
  if (
      overview.value?.twoFactorEnabled
  ) {
    disableTwoFactorCode.value = ''
    disableTwoFactorError.value = ''

    confirmation.value = {
      kind: 'disable-2fa',
    }

    return
  }

  twoFactorCode.value = ''
  twoFactorError.value = ''
  twoFactorLoading.value = true

  try {
    twoFactorSetup.value =
        await securityService
            .startTwoFactorSetup()

    twoFactorOpen.value = true
  } catch (caught) {
    error.value =
        readableError(
            caught,
            'ساخت کد ورود دومرحله‌ای انجام نشد.',
        )
  } finally {
    twoFactorLoading.value = false
  }
}

function updateTwoFactorCode(
    value: string,
): void {
  twoFactorCode.value =
      normalizeDigits(value)
          .replace(/\D/g, '')
          .slice(0, 6)

  twoFactorError.value = ''
}

function updateDisableTwoFactorCode(
    value: string,
): void {
  disableTwoFactorCode.value =
      normalizeDigits(value)
          .replace(/\D/g, '')
          .slice(0, 6)

  disableTwoFactorError.value = ''
}

async function enableTwoFactor(): Promise<void> {
  const code =
      normalizeDigits(
          twoFactorCode.value,
      )
          .replace(/\D/g, '')
          .slice(0, 6)

  if (!twoFactorSetup.value) {
    twoFactorError.value =
        'درخواست فعال‌سازی منقضی شده است؛ دوباره شروع کنید.'
    return
  }

  if (!/^\d{6}$/.test(code)) {
    twoFactorError.value =
        'کد ۶ رقمی برنامه تأییدکننده را وارد کنید.'
    return
  }

  twoFactorLoading.value = true

  try {
    overview.value =
        await securityService.setTwoFactor(
            true,
            code,
            twoFactorSetup.value.setupToken,
        )

    events.value =
        await securityService.listEvents()

    twoFactorOpen.value = false
    twoFactorSetup.value = null
    twoFactorCode.value = ''
    twoFactorError.value = ''

    feedback.value =
        'ورود دومرحله‌ای فعال شد.'
  } catch (caught) {
    twoFactorError.value =
        readableError(
            caught,
            'فعال‌سازی ورود دومرحله‌ای انجام نشد.',
        )
  } finally {
    twoFactorLoading.value = false
  }
}

async function openPhishing(): Promise<void> {
  phishingError.value = ''
  phishingLoading.value = true

  try {
    const latestOverview =
        await securityService.getOverview()

    overview.value =
        latestOverview

    const existingCode =
        String(
            latestOverview.antiPhishingCode ??
            '',
        ).trim()

    phishingCode.value =
        existingCode

    phishingMode.value =
        existingCode.length > 0
            ? 'existing'
            : 'create'

    phishingOpen.value = true
  } catch (caught) {
    error.value =
        readableError(
            caught,
            'اطلاعات کد ضد فیشینگ دریافت نشد.',
        )
  } finally {
    phishingLoading.value = false
  }
}

function updatePhishingCode(
    value: string,
): void {
  if (
      phishingMode.value === 'existing'
  ) {
    return
  }

  phishingCode.value =
      value.slice(0, 20)

  phishingError.value = ''
}

async function savePhishing(): Promise<void> {
  if (
      phishingMode.value !== 'create'
  ) {
    return
  }

  const code =
      phishingCode.value.trim()

  if (
      code &&
      (
          code.length < 4 ||
          code.length > 20
      )
  ) {
    phishingError.value =
        'عبارت باید بین ۴ تا ۲۰ کاراکتر باشد.'
    return
  }

  phishingLoading.value = true
  phishingError.value = ''

  try {
    const updatedOverview =
        await securityService
            .setAntiPhishingCode(
                code || null,
            )

    overview.value =
        updatedOverview

    events.value =
        await securityService.listEvents()

    if (code) {
      phishingMode.value =
          'existing'
      phishingCode.value =
          code
    } else {
      phishingMode.value =
          'create'
      phishingCode.value =
          ''
    }

    phishingOpen.value = false

    feedback.value = code
        ? 'کد ضد فیشینگ ذخیره شد.'
        : 'کد ضد فیشینگ حذف شد.'
  } catch (caught) {
    phishingError.value =
        readableError(
            caught,
            'ذخیره کد ضد فیشینگ انجام نشد.',
        )
  } finally {
    phishingLoading.value = false
  }
}

async function removePhishing(): Promise<void> {
  phishingLoading.value = true
  phishingError.value = ''

  try {
    const updatedOverview =
        await securityService
            .setAntiPhishingCode(
                null,
            )

    overview.value =
        updatedOverview

    events.value =
        await securityService.listEvents()

    phishingCode.value = ''
    phishingMode.value = 'create'

    feedback.value =
        'کد ضد فیشینگ حذف شد.'
  } catch (caught) {
    phishingError.value =
        readableError(
            caught,
            'حذف کد ضد فیشینگ انجام نشد.',
        )
  } finally {
    phishingLoading.value = false
  }
}

function closeConfirmation(): void {
  if (confirming.value) {
    return
  }

  confirmation.value = null
  disableTwoFactorCode.value = ''
  disableTwoFactorError.value = ''
}

async function runConfirmation(): Promise<void> {
  const action =
      confirmation.value

  if (!action) {
    return
  }

  let disableCode = ''

  if (
      action.kind === 'disable-2fa'
  ) {
    disableCode =
        normalizeDigits(
            disableTwoFactorCode.value,
        )
            .replace(/\D/g, '')
            .slice(0, 6)

    if (!/^\d{6}$/.test(disableCode)) {
      disableTwoFactorError.value =
          'کد ۶ رقمی برنامه Authenticator را وارد کنید.'
      return
    }
  }

  confirming.value = true
  error.value = ''

  try {
    if (action.kind === 'session') {
      await securityService.revokeSession(
          action.session.id,
      )

      sessions.value =
          sessions.value.filter(
              (session) =>
                  session.id !==
                  action.session.id,
          )

      feedback.value =
          `دسترسی ${action.session.deviceName} قطع شد.`
    } else if (
        action.kind ===
        'other-sessions'
    ) {
      await securityService
          .revokeOtherSessions()

      sessions.value =
          sessions.value.filter(
              (session) =>
                  session.current,
          )

      feedback.value =
          'همه نشست‌های دیگر پایان یافتند.'
    } else if (
        action.kind === 'disable-2fa'
    ) {
      overview.value =
          await securityService.setTwoFactor(
              false,
              disableCode,
          )

      events.value =
          await securityService.listEvents()

      disableTwoFactorCode.value =
          ''
      disableTwoFactorError.value =
          ''

      feedback.value =
          'ورود دومرحله‌ای غیرفعال شد.'
    } else if (
        action.kind === 'whitelist'
    ) {
      overview.value =
          await securityService
              .setWithdrawalWhitelist(
                  action.enabled,
              )

      events.value =
          await securityService.listEvents()

      feedback.value =
          action.enabled
              ? 'فهرست مجاز برداشت فعال شد.'
              : 'فهرست مجاز برداشت غیرفعال شد.'
    }

    if (
        action.kind === 'session' ||
        action.kind ===
        'other-sessions'
    ) {
      overview.value =
          await securityService
              .getOverview()

      events.value =
          await securityService
              .listEvents()
    }

    confirmation.value = null
  } catch (caught) {
    if (
        action.kind ===
        'disable-2fa'
    ) {
      disableTwoFactorError.value =
          readableError(
              caught,
              'کد Authenticator صحیح نیست یا منقضی شده است.',
          )
    } else {
      error.value =
          readableError(
              caught,
              'تغییر امنیتی انجام نشد.',
          )

      confirmation.value = null
    }
  } finally {
    confirming.value = false
  }
}

function onWhitelistInput(
    enabled: boolean,
): void {
  if (
      !overview.value ||
      enabled ===
      overview.value
          .withdrawalWhitelistEnabled
  ) {
    return
  }

  confirmation.value = {
    kind: 'whitelist',
    enabled,
  }
}

watch(
    withdrawalAddressAsset,
    (symbol) => {
      void loadWithdrawalNetworks(
          symbol,
      )
    },
)

onMounted(() => {
  withdrawalAddressClockTimer =
      window.setInterval(() => {
        withdrawalAddressNowMs.value =
            Date.now()
      }, 1_000)

  void load()
})

onBeforeUnmount(() => {
  if (
      withdrawalAddressClockTimer !==
      undefined
  ) {
    window.clearInterval(
        withdrawalAddressClockTimer,
    )
  }
})
</script>

<template>
  <div class="page security-page">
    <PageHeader
        title="امنیت حساب"
        description="ورودها، دستگاه‌ها و لایه‌های حفاظتی دارایی خود را مدیریت کنید."
    >
      <template #actions>
        <AppButton
            variant="secondary"
            size="sm"
            icon="refresh"
            :loading="loading"
            @click="load()"
        >
          به‌روزرسانی
        </AppButton>
      </template>
    </PageHeader>

    <div
        v-if="feedback"
        class="notice success"
        role="status"
    >
      <AppIcon
          name="check"
          :size="19"
      />

      <span>{{ feedback }}</span>

      <button
          type="button"
          aria-label="بستن"
          @click="feedback = ''"
      >
        <AppIcon
            name="close"
            :size="16"
        />
      </button>
    </div>

    <div
        v-if="error"
        class="notice danger"
        role="alert"
    >
      <AppIcon
          name="warning"
          :size="19"
      />

      <span>{{ error }}</span>

      <button
          type="button"
          @click="load()"
      >
        تلاش دوباره
      </button>
    </div>

    <template v-if="loading">
      <AppCard padding="lg">
        <div class="score-skeleton">
          <AppSkeleton
              width="7rem"
              height="7rem"
              radius="50%"
          />

          <div>
            <AppSkeleton
                width="12rem"
                height="1.6rem"
            />

            <AppSkeleton
                width="21rem"
                height=".9rem"
            />
          </div>
        </div>
      </AppCard>

      <div class="security-grid">
        <AppCard
            v-for="i in 2"
            :key="i"
            padding="lg"
        >
          <AppSkeleton
              v-for="j in 4"
              :key="j"
              height="4.5rem"
              :style="{
              marginBottom: '1rem',
            }"
          />
        </AppCard>
      </div>
    </template>

    <template v-else-if="overview">
      <AppCard
          class="score-card"
          padding="lg"
          :class="`score-${scoreTone}`"
      >
        <div
            class="score-ring"
            :style="{
            '--score-angle':
              `${overview.score * 3.6}deg`,
          }"
            role="progressbar"
            aria-label="امتیاز امنیت حساب"
            aria-valuemin="0"
            aria-valuemax="100"
            :aria-valuenow="overview.score"
        >
          <span>
            <strong>
              {{ toPersianDigits(overview.score) }}
            </strong>

            <small>
              از ۱۰۰
            </small>
          </span>
        </div>

        <div class="score-copy">
          <span>
            وضعیت حفاظت حساب
          </span>

          <h2>
            {{ scoreLabel }}
          </h2>

          <p>
            با فعال‌کردن ورود دومرحله‌ای و کنترل
            نشست‌های ناشناس، امنیت حساب را بالاتر ببرید.
          </p>
        </div>

        <div class="score-facts">
          <div>
            <AppIcon
                name="phone"
                :size="19"
            />

            <span>
              <small>
                موبایل
              </small>

              <strong>
                {{
                  overview.mobileVerified
                      ? 'تأییدشده'
                      : 'تأییدنشده'
                }}
              </strong>
            </span>
          </div>

          <div>
            <AppIcon
                name="shield"
                :size="19"
            />

            <span>
              <small>
                ورود دومرحله‌ای
              </small>

              <strong>
                {{
                  overview.twoFactorEnabled
                      ? 'فعال'
                      : 'غیرفعال'
                }}
              </strong>
            </span>
          </div>

          <div>
            <AppIcon
                name="markets"
                :size="19"
            />

            <span>
              <small>
                نشست فعال
              </small>

              <strong>
                {{
                  toPersianDigits(
                      overview.activeSessionsCount,
                  )
                }}
                دستگاه
              </strong>
            </span>
          </div>
        </div>
      </AppCard>

      <div class="security-grid">
        <AppCard
            padding="lg"
            class="protection-card"
        >
          <div class="section-heading">
            <span>
              <AppIcon
                  name="lock"
                  :size="21"
              />
            </span>

            <div>
              <h2>
                ورود و بازیابی
              </h2>

              <p>
                راه‌های ورود و تأیید هویت حساب
              </p>
            </div>
          </div>

          <div class="setting-list">
            <div class="setting-row">
              <span class="setting-icon">
                <AppIcon
                    name="lock"
                    :size="21"
                />
              </span>

              <div>
                <strong>
                  رمز عبور
                </strong>

                <small>
                  برای حساب شما تنظیم شده است
                </small>
              </div>

              <StatusBadge
                  domain="security"
                  status="secure"
              />

              <AppButton
                  variant="secondary"
                  size="sm"
                  icon="edit"
                  @click="openPassword"
              >
                تغییر رمز
              </AppButton>
            </div>

            <div
                class="setting-row featured"
            >
              <span class="setting-icon">
                <AppIcon
                    name="shield"
                    :size="21"
                />
              </span>

              <div>
                <strong>
                  ورود دومرحله‌ای
                </strong>

                <small>
                  تأیید ورود با کد برنامه Authenticator
                </small>
              </div>

              <StatusBadge
                  domain="security"
                  :status="
                  overview.twoFactorEnabled
                    ? 'enabled'
                    : 'disabled'
                "
              />

              <AppButton
                  :variant="
                  overview.twoFactorEnabled
                    ? 'ghost'
                    : 'primary'
                "
                  size="sm"
                  @click="requestTwoFactorChange"
              >
                {{
                  overview.twoFactorEnabled
                      ? 'غیرفعال‌سازی'
                      : 'فعال‌سازی'
                }}
              </AppButton>
            </div>

            <div class="setting-row">
              <span class="setting-icon">
                <AppIcon
                    name="phone"
                    :size="21"
                />
              </span>

              <div>
                <strong>
                  شماره موبایل
                </strong>

                <small>
                  برای کدهای امنیتی و بازیابی
                </small>
              </div>

              <StatusBadge
                  domain="security"
                  :status="
                  overview.mobileVerified
                    ? 'verified'
                    : 'unverified'
                "
              />

              <span class="row-note">
                {{
                  overview.mobileVerified
                      ? 'نیاز به اقدام نیست'
                      : 'تکمیل در احراز هویت'
                }}
              </span>
            </div>

            <div class="setting-row">
              <span class="setting-icon">
                <AppIcon
                    name="mail"
                    :size="21"
                />
              </span>

              <div>
                <strong>
                  نشانی ایمیل
                </strong>

                <small>
                  برای هشدارهای ورود و بازیابی
                </small>
              </div>

              <StatusBadge
                  domain="security"
                  :status="
                  overview.emailVerified
                    ? 'verified'
                    : 'unverified'
                "
              />

              <AppButton
                  v-if="
                  !overview.emailVerified
                "
                  to="/app/profile"
                  variant="ghost"
                  size="sm"
              >
                بررسی ایمیل
              </AppButton>

              <span
                  v-else
                  class="row-note"
              >
                تأییدشده
              </span>
            </div>
          </div>
        </AppCard>

        <AppCard
            padding="lg"
            class="withdrawal-security"
        >
          <div class="section-heading">
            <span>
              <AppIcon
                  name="wallet"
                  :size="21"
              />
            </span>

            <div>
              <h2>
                امنیت برداشت
              </h2>

              <p>
                کنترل‌های تکمیلی برای خروج دارایی
              </p>
            </div>
          </div>

          <div
              class="feature-block phishing-feature"
          >
            <div class="feature-title">
              <span>
                <AppIcon
                    name="mail"
                    :size="21"
                />
              </span>

              <div>
                <strong>
                  کد ضد فیشینگ
                </strong>

                <small>
                  نمایش عبارت اختصاصی شما در پیام‌های معتبر روشا
                </small>
              </div>
            </div>

            <div class="phishing-status-row">
              <StatusBadge
                  domain="security"
                  :status="
                  overview.antiPhishingEnabled
                    ? 'enabled'
                    : 'disabled'
                "
              />
            </div>

            <AppButton
                class="phishing-action"
                variant="secondary"
                size="sm"
                :loading="phishingLoading"
                icon="edit"
                @click="openPhishing"
            >
              {{
                overview.antiPhishingEnabled
                    ? 'مشاهده کد'
                    : 'تنظیم عبارت'
              }}
            </AppButton>
          </div>

          <div
              class="feature-block whitelist-feature"
          >
            <div class="feature-header">
              <div class="feature-title">
                <span>
                  <AppIcon
                      name="check"
                      :size="21"
                  />
                </span>

                <div>
                  <strong>
                    فهرست مجاز آدرس برداشت
                  </strong>

                  <small>
                    آدرس‌های مورد تأیید شما برای برداشت
                  </small>
                </div>
              </div>

              <AppSwitch
                  :model-value="
                  overview.withdrawalWhitelistEnabled
                "
                  :label="
                  overview.withdrawalWhitelistEnabled
                    ? 'فعال'
                    : 'غیرفعال'
                "
                  description="تغییر این گزینه نیازمند تأیید شماست."
                  @update:model-value="
                  onWhitelistInput
                "
              />
            </div>

            <div
                class="whitelist-description"
            >
              <AppIcon
                  name="shield"
                  :size="17"
              />

              <span>
                هنگام افزودن آدرس، ابتدا ارز و شبکه را انتخاب می‌کنید و سپس
                آدرس را وارد می‌کنید. تطابق ارز، شبکه، ساختار آدرس و شرایط
                Memo/Tag در سرور بررسی می‌شود و پس از OTP و در صورت نیاز
                Authenticator، آدرس وارد دوره امنیتی می‌شود.
              </span>
            </div>

            <div
                class="address-management-header"
            >
              <div>
                <strong>
                  آدرس‌های ثبت‌شده
                </strong>

                <small>
                  {{
                    toPersianDigits(
                        visibleWithdrawalAddresses.length,
                    )
                  }}
                  آدرس
                </small>
              </div>

              <AppButton
                  variant="secondary"
                  size="sm"
                  icon="plus"
                  :disabled="
                  !overview.mobileVerified
                "
                  @click="
                  openWithdrawalAddressModal
                "
              >
                افزودن آدرس
              </AppButton>
            </div>

            <div
                v-if="
                !overview.mobileVerified
              "
                class="address-warning"
            >
              <AppIcon
                  name="warning"
                  :size="17"
              />

              <span>
                برای افزودن آدرس برداشت ابتدا شماره موبایل خود را تأیید کنید.
              </span>
            </div>

            <div
                v-if="
                withdrawalAddressesLoading
              "
                class="address-loading"
            >
              <AppSkeleton
                  v-for="i in 2"
                  :key="i"
                  height="3.5rem"
                  radius="var(--radius-md)"
              />
            </div>

            <div
                v-else-if="
                visibleWithdrawalAddresses.length
              "
                class="withdrawal-address-list"
            >
              <button
                  v-for="
                  (address, index) in
                  visibleWithdrawalAddresses
                "
                  :key="address.id"
                  type="button"
                  class="withdrawal-address-link"
                  :class="{
                  'is-default':
                    address.isDefault,
                }"
                  @click="
                  openWithdrawalAddressDetails(
                      address,
                  )
                "
              >
                <span
                    class="withdrawal-address-link__icon"
                >
                  <AppIcon
                      name="wallet"
                      :size="17"
                  />
                </span>

                <span
                    class="withdrawal-address-link__copy"
                >
                  آدرس
                  {{
                    toPersianDigits(
                        index + 1,
                    )
                  }}
                </span>

                <span
                    v-if="address.isDefault"
                    class="withdrawal-address-link__default"
                >
                  پیش‌فرض
                </span>

                <AppIcon
                    name="chevronLeft"
                    :size="17"
                />
              </button>
            </div>

            <EmptyState
                v-else
                icon="wallet"
                title="آدرسی ثبت نشده است"
                description="برای استفاده از فهرست مجاز، یک آدرس برداشت معتبر ثبت و تأیید کنید."
            >
              <AppButton
                  variant="secondary"
                  :disabled="
                  !overview.mobileVerified
                "
                  @click="
                  openWithdrawalAddressModal
                "
              >
                افزودن اولین آدرس
              </AppButton>
            </EmptyState>

            <p
                v-if="
                withdrawalAddressCreateError
              "
                class="modal-error"
                role="alert"
            >
              {{
                withdrawalAddressCreateError
              }}
            </p>
          </div>
        </AppCard>

        <AppCard
            padding="none"
            class="events-card"
        >
          <header class="list-header">
            <div>
              <span>
                <AppIcon
                    name="clock"
                    :size="21"
                />
              </span>

              <div>
                <h2>
                  تاریخچه امنیتی
                </h2>

                <p>
                  آخرین ورودها و تغییرات مهم حساب
                </p>
              </div>
            </div>
          </header>

          <div
              v-if="events.length"
              class="event-list"
          >
            <article
                v-for="event in events"
                :key="event.id"
            >
              <span
                  class="event-icon"
                  :class="
                  `tone-${eventTone(event.type)}`
                "
              >
                <AppIcon
                    :name="
                    eventIcon(event.type)
                  "
                    :size="20"
                />
              </span>

              <div>
                <h3>
                  {{ event.title }}
                </h3>

                <p>
                  {{ event.description }}
                </p>

                <small>
                  {{ event.deviceName }} ·

                  <bdi dir="ltr">
                    {{ event.ipAddress }}
                  </bdi>
                </small>
              </div>

              <time
                  class="event-time"
                  :datetime="event.createdAt"
              >
                <strong>
                  {{
                    formatSecurityEventTime(
                        event.createdAt,
                    )
                  }}
                </strong>

                <small>
                  {{
                    formatPersianDateTime(
                        event.createdAt,
                    )
                  }}
                </small>
              </time>
            </article>
          </div>

          <EmptyState
              v-else
              icon="clock"
              title="رویداد امنیتی ثبت نشده"
              description="ورودها و تغییرات امنیتی مهم در این بخش نمایش داده می‌شوند."
          />
        </AppCard>
      </div>

      <AppCard
          padding="none"
          class="sessions-card"
      >
        <header class="list-header">
          <div>
            <span>
              <AppIcon
                  name="markets"
                  :size="21"
              />
            </span>

            <div>
              <h2>
                دستگاه‌های فعال
              </h2>

              <p>
                اگر دستگاهی را نمی‌شناسید، فوراً دسترسی
                آن را قطع و رمز عبور را تغییر دهید.
              </p>
            </div>
          </div>

          <AppButton
              v-if="otherSessionCount"
              variant="danger"
              size="sm"
              icon="logout"
              @click="
              confirmation = {
                kind: 'other-sessions',
              }
            "
          >
            خروج از سایر دستگاه‌ها
          </AppButton>
        </header>

        <div class="session-list">
          <article
              v-for="session in sessions"
              :key="session.id"
              class="session-row"
              :class="{
              current: session.current,
            }"
          >
            <span class="device-icon">
              <AppIcon
                  :name="
                  deviceIcon(
                    session.deviceType,
                  )
                "
                  :size="23"
              />
            </span>

            <div class="session-copy">
              <div
                  class="session-device-line"
              >
                <h3>
                  {{ session.browser }} روی
                  {{ session.os }}
                </h3>

                <StatusBadge
                    v-if="session.current"
                    domain="security"
                    status="current"
                />
              </div>

              <span>
                <bdi dir="ltr">
                  {{ session.ipAddress }}
                </bdi>

                <i
                    v-if="
                    session.approximateLocation
                  "
                />

                {{
                  session.approximateLocation
                }}
              </span>
            </div>

            <div class="session-time">
              <small>
                آخرین فعالیت
              </small>

              <strong
                  :title="
                  formatPersianDateTime(
                    session.lastActiveAt,
                  )
                "
              >
                {{
                  session.current
                      ? 'همین حالا'
                      : formatRelativeTime(
                          session.lastActiveAt,
                      )
                }}
              </strong>
            </div>

            <AppButton
                v-if="!session.current"
                variant="danger"
                size="sm"
                icon="logout"
                @click="
                confirmation = {
                  kind: 'session',
                  session,
                }
              "
            >
              قطع دسترسی
            </AppButton>
          </article>
        </div>
      </AppCard>
    </template>

    <AppModal
        v-model="withdrawalAddressModalOpen"
        title="افزودن آدرس برداشت"
        description="ابتدا ارز و شبکه را انتخاب کنید، سپس آدرس مقصد را وارد کنید."
        size="md"
        :dismissible="
        !withdrawalAddressCreating
      "
    >
      <form
          class="modal-form"
          @submit.prevent="
          createWithdrawalAddress
        "
      >
        <div
            class="address-create-network"
        >
          <span>
            روند ثبت
          </span>

          <strong>
            ارز ← شبکه ← آدرس ← تأیید امنیتی
          </strong>

          <small>
            تطابق آدرس با ارز و شبکه در سمت سرور بررسی می‌شود.
          </small>
        </div>

        <AssetSelect
            v-model="withdrawalAddressAsset"
            :assets="cryptoWalletAssets"
            :balances="
            withdrawalAssetBalances
          "
            :disabled-symbols="
            disabledWithdrawalAssetSymbols
          "
            :disabled-descriptions="
            disabledWithdrawalAssetDescriptions
          "
            label="ارز"
            balance-label="قابل برداشت"
            show-balance
            required
        />

        <NetworkSelector
            :model-value="
            withdrawalAddressNetwork
          "
            :networks="
            withdrawalNetworks
          "
            mode="withdrawal"
            label="شبکه"
            :error="
            withdrawalAddressCreateError
          "
            :disabled="
            !withdrawalAddressAsset ||
            withdrawalNetworkLoading
          "
            @update:model-value="
            (value) => {
              withdrawalAddressNetwork =
                value
              withdrawalAddressValue =
                ''
              withdrawalAddressMemo =
                ''
              withdrawalAddressError =
                ''
              withdrawalAddressMemoError =
                ''
            }
          "
        />

        <AppInput
            v-model="
            withdrawalAddressValue
          "
            label="آدرس کیف پول مقصد"
            placeholder="آدرس را وارد یا جای‌گذاری کنید"
            :error="
            withdrawalAddressError
          "
            ltr
            autocomplete="off"
            icon="wallet"
        />

        <AppInput
            v-if="
            selectedWithdrawalNetwork?.memoRequired
          "
            v-model="
            withdrawalAddressMemo
          "
            label="ممو / تگ مقصد"
            placeholder="ممو یا تگ را دقیقاً وارد کنید"
            :error="
            withdrawalAddressMemoError
          "
            ltr
            autocomplete="off"
        />

        <AppInput
            v-model="
            withdrawalAddressLabel
          "
            label="عنوان آدرس"
            placeholder="مثلاً کیف پول شخصی"
            :error="
            withdrawalAddressLabelError
          "
        />

        <div
            class="address-create-hint"
        >
          <AppIcon
              name="shield"
              :size="17"
          />

          <span>
            آدرس پس از اعتبارسنجی سرور با کد پیامکی تأیید می‌شود.
            اگر Authenticator فعال باشد، کد آن نیز لازم خواهد بود.
          </span>
        </div>

        <div
            v-if="
            withdrawalAddressCreateError
          "
            class="modal-error"
            role="alert"
        >
          {{
            withdrawalAddressCreateError
          }}
        </div>
      </form>

      <template #footer>
        <div class="withdrawal-modal-actions">
          <AppButton
              :loading="withdrawalAddressCreating"
              @click="createWithdrawalAddress"
          >
            ثبت آدرس و ارسال کد تأیید
          </AppButton>

          <AppButton
              variant="secondary"
              :disabled="withdrawalAddressCreating"
              @click="closeWithdrawalAddressModal"
          >
            انصراف
          </AppButton>
        </div>
      </template>
    </AppModal>

    <AppModal
        v-model="withdrawalAddressDetailsOpen"
        title="جزئیات آدرس برداشت"
        description="اطلاعات آدرس انتخاب‌شده را بررسی کنید."
        size="sm"
        :dismissible="!withdrawalAddressActionLoading"
        @update:model-value="
        (value) => {
          if (!value) {
            closeWithdrawalAddressDetails()
          }
        }
      "
    >
      <div
          v-if="selectedWithdrawalAddress"
          class="withdrawal-address-details"
      >
        <div class="withdrawal-address-detail-row">
          <span>نام</span>

          <strong>
            {{
              selectedWithdrawalAddress.label ||
              'آدرس برداشت'
            }}
          </strong>
        </div>

        <div class="withdrawal-address-detail-row">
          <span>ارز</span>

          <strong>
            {{
              selectedWithdrawalAddress.assetNameFa
            }}
          </strong>
        </div>

        <div class="withdrawal-address-detail-row">
          <span>شبکه</span>

          <strong>
            {{
              selectedWithdrawalAddress.networkDisplayName
            }}
          </strong>
        </div>

        <div
            class="withdrawal-address-detail-block"
        >
          <span>آدرس</span>

          <bdi dir="ltr">
            {{
              selectedWithdrawalAddress.address
            }}
          </bdi>
        </div>

        <div
            v-if="selectedWithdrawalAddress.memo"
            class="withdrawal-address-detail-block"
        >
          <span>Memo / Tag</span>

          <bdi dir="ltr">
            {{
              selectedWithdrawalAddress.memo
            }}
          </bdi>
        </div>

        <div
            class="withdrawal-address-detail-status"
        >
          <div>
            <span>وضعیت</span>

            <strong
                class="address-status"
                :class="
                `tone-${withdrawalAddressStatusTone(
                    selectedWithdrawalAddress.status,
                )}`
              "
            >
              {{
                withdrawalAddressStatusLabel(
                    selectedWithdrawalAddress.status,
                )
              }}
            </strong>
          </div>

          <div>
            <span>آدرس پیش‌فرض</span>

            <strong>
              {{
                selectedWithdrawalAddress.isDefault
                    ? 'بله'
                    : 'خیر'
              }}
            </strong>
          </div>
        </div>

        <div
            v-if="
            selectedWithdrawalAddress.status ===
                'cooling_down' &&
            selectedWithdrawalAddress.cooldownUntil
          "
            class="withdrawal-address-detail-note"
        >
          <AppIcon
              name="clock"
              :size="15"
          />

          <span>
            {{
              formatCooldownRemaining(
                  cooldownSecondsRemaining(
                      selectedWithdrawalAddress,
                  ),
              )
            }}
            باقی‌مانده
          </span>
        </div>
      </div>

      <template #footer>
        <AppButton
            v-if="
            selectedWithdrawalAddress &&
            selectedWithdrawalAddress.status === 'active' &&
            !selectedWithdrawalAddress.isDefault
          "
            block
            :loading="
            withdrawalAddressActionLoading ===
            `default:${selectedWithdrawalAddress.id}`
          "
            @click="
            setSelectedWithdrawalAddressDefault
          "
        >
          انتخاب به‌عنوان پیش‌فرض
        </AppButton>

        <div
            v-else-if="
            selectedWithdrawalAddress?.isDefault
          "
            class="withdrawal-address-detail-default"
        >
          آدرس پیش‌فرض انتخاب شده است
        </div>

        <AppButton
            variant="secondary"
            :disabled="Boolean(withdrawalAddressActionLoading)"
            @click="closeWithdrawalAddressDetails"
        >
          بستن
        </AppButton>
      </template>
    </AppModal>

    <AppModal
        v-model="
        withdrawalAddressConfirmationOpen
      "
        title="تأیید آدرس برداشت"
        description="کد ارسال‌شده را وارد کنید تا آدرس وارد مرحله امنیتی شود."
        size="sm"
        :dismissible="
        !withdrawalAddressConfirming
      "
    >
      <div
          class="address-confirmation-step"
      >
        <div class="phone-mark">
          <AppIcon
              name="phone"
              :size="25"
          />
        </div>

        <p>
          کد تأیید به شماره
          {{
            withdrawalAddressConfirmation
                ?.destinationHint ||
            'ثبت‌شده شما'
          }}
          ارسال شد.
        </p>

        <div
            class="review-address"
        >
          <span>
            آدرس مقصد
          </span>

          <bdi dir="ltr">
            {{
              pendingWithdrawalAddressPreview
            }}
          </bdi>
        </div>

        <OtpInput
            :model-value="
            withdrawalAddressOtp
          "
            label="کد تأیید آدرس"
            :error="
            withdrawalAddressOtpError
          "
            :loading="
            withdrawalAddressConfirming
          "
            :resend-loading="
            withdrawalAddressResending
          "
            :countdown-seconds="
            withdrawalAddressResendDelay
          "
            @update:model-value="
            (value: string) => {
              withdrawalAddressOtp =
                normalizeDigits(value)
                  .replace(/\D/g, '')
                  .slice(0, 6)
              withdrawalAddressOtpError =
                ''
            }
          "
            @resend="
            resendWithdrawalAddressConfirmation
          "
        />

        <DemoCodeHint
            v-if="DemoCodeHint"
            context="withdrawal"
        />

        <p
            v-if="
            withdrawalAddressConfirmationExpired
          "
            class="challenge-expiry expired"
        >
          مهلت کد تأیید تمام شده است؛ ارسال مجدد را بزنید.
        </p>

        <p
            v-else-if="
            withdrawalAddressConfirmation
          "
            class="challenge-expiry"
        >
          اعتبار کد:
          {{
            toPersianDigits(
                withdrawalAddressConfirmationSecondsRemaining,
            )
          }}
          ثانیه
        </p>

        <AppInput
            v-if="
            overview?.twoFactorEnabled
          "
            :model-value="
            withdrawalAddressTwoFactorCode
          "
            label="کد برنامه Authenticator"
            inputmode="numeric"
            autocomplete="one-time-code"
            maxlength="6"
            placeholder="••••••"
            ltr
            :error="
            withdrawalAddressTwoFactorError
          "
            @update:model-value="
            (value: string) => {
              withdrawalAddressTwoFactorCode =
                normalizeDigits(value)
                  .replace(/\D/g, '')
                  .slice(0, 6)
              withdrawalAddressTwoFactorError =
                ''
            }
          "
        />

        <p
            v-if="
            withdrawalAddressSecurityMessage
          "
            class="security-message"
            role="status"
        >
          {{
            withdrawalAddressSecurityMessage
          }}
        </p>
      </div>

      <template #footer>
        <AppButton
            block
            :loading="
            withdrawalAddressConfirming
          "
            :disabled="
            withdrawalAddressConfirmationExpired
          "
            @click="
            confirmWithdrawalAddress
          "
        >
          تأیید آدرس
        </AppButton>
      </template>
    </AppModal>

    <AppModal
        v-model="passwordOpen"
        title="تغییر رمز عبور"
        description="رمزی انتخاب کنید که در سرویس دیگری استفاده نمی‌کنید."
        size="sm"
        :dismissible="
        !changingPassword
      "
    >
      <form
          class="modal-form"
          @submit.prevent="changePassword"
      >
        <div
            v-if="passwordError"
            class="modal-error"
            role="alert"
        >
          {{ passwordError }}
        </div>

        <AppInput
            v-model="
            passwordForm.currentPassword
          "
            type="password"
            label="رمز عبور فعلی"
            autocomplete="current-password"
            :error="
            passwordFields.currentPassword
          "
        />

        <AppInput
            v-model="
            passwordForm.newPassword
          "
            type="password"
            label="رمز عبور جدید"
            autocomplete="new-password"
            hint="حداقل ۸ کاراکتر"
            :error="
            passwordFields.newPassword
          "
        />

        <AppInput
            v-model="
            passwordForm.newPasswordConfirmation
          "
            type="password"
            label="تکرار رمز عبور جدید"
            autocomplete="new-password"
            :error="
            passwordFields
              .newPasswordConfirmation
          "
        />
      </form>

      <template #footer>
        <AppButton
            block
            :loading="changingPassword"
            @click="changePassword"
        >
          تغییر رمز عبور
        </AppButton>

        <AppButton
            variant="secondary"
            :disabled="changingPassword"
            @click="
            passwordOpen = false
          "
        >
          انصراف
        </AppButton>
      </template>
    </AppModal>

    <AppModal
        v-model="twoFactorOpen"
        title="فعال‌سازی ورود دومرحله‌ای"
        description="کد QR را فقط در برنامه Authenticator خود اسکن کنید."
        size="md"
        :dismissible="
        !twoFactorLoading
      "
    >
      <form
          class="modal-form"
          @submit.prevent="enableTwoFactor"
      >
        <div
            v-if="twoFactorSetup"
            class="two-factor-setup"
        >
          <div class="two-factor-qr">
            <QrCode
                :value="
                twoFactorSetup.otpauthUri
              "
                :size="156"
                label="کد QR راه‌اندازی ورود دومرحله‌ای"
            />
          </div>

          <div
              class="two-factor-manual"
          >
            <strong>
              ۱. اسکن یا ورود دستی
            </strong>

            <p>
              کد را در Google Authenticator،
              Microsoft Authenticator یا برنامه مشابه
              وارد کنید.
            </p>

            <span class="setup-secret">
              <bdi>
                {{ twoFactorSetup.secret }}
              </bdi>

              <CopyButton
                  :value="
                  twoFactorSetup.secret
                "
                  label="کپی کلید"
              />
            </span>
          </div>
        </div>

        <div class="auth-guide">
          <span>
            <AppIcon
                name="shield"
                :size="27"
            />
          </span>

          <div>
            <strong>
              ۲. تأیید اتصال برنامه
            </strong>

            <DemoCodeHint
                v-if="DemoCodeHint"
                context="two-factor"
            />

            <p v-else>
              کد شش‌رقمی فعلی برنامه را برای تکمیل
              اتصال وارد کنید.
            </p>
          </div>
        </div>

        <AppInput
            :model-value="
            twoFactorCode
          "
            label="کد ۶ رقمی برنامه"
            inputmode="numeric"
            autocomplete="one-time-code"
            maxlength="6"
            ltr
            :error="twoFactorError"
            placeholder="••••••"
            @update:model-value="
            updateTwoFactorCode
          "
        />
      </form>

      <template #footer>
        <div class="two-factor-actions">
          <AppButton
              :loading="twoFactorLoading"
              @click="enableTwoFactor"
          >
            تأیید و فعال‌سازی
          </AppButton>

          <AppButton
              variant="secondary"
              :disabled="twoFactorLoading"
              @click="
              twoFactorOpen = false
            "
          >
            انصراف
          </AppButton>
        </div>
      </template>
    </AppModal>

    <AppModal
        v-model="phishingOpen"
        title="کد ضد فیشینگ"
        description="این عبارت باید در پیام‌های معتبر روشا نمایش داده شود."
        size="sm"
        :dismissible="
        !phishingLoading
      "
    >
      <form
          class="modal-form"
          @submit.prevent="
          phishingMode === 'create'
            ? savePhishing()
            : undefined
        "
      >
        <AppInput
            :model-value="
            phishingCode
          "
            label="عبارت اختصاصی شما :"
            :placeholder="
            phishingMode === 'create'
              ? 'مثلاً: rosha-arya'
              : ''
          "
            :readonly="
            phishingMode === 'existing'
          "
            ltr
            :error="phishingError"
            :hint="
            phishingMode === 'existing'
              ? 'کد فعلی ضد فیشینگ شما'
              : 'بین ۴ تا ۲۰ کاراکتر و قابل تشخیص برای خودتان'
          "
            @update:model-value="
            updatePhishingCode
          "
        />

        <div class="phishing-help">
          <AppIcon
              name="warning"
              :size="18"
          />

          <span>
            اگر پیامی این عبارت را نداشت،
            روی لینک‌های آن کلیک نکنید.
          </span>
        </div>
      </form>

      <template #footer>
        <template
            v-if="
            phishingMode === 'create'
          "
        >
          <AppButton
              block
              :loading="phishingLoading"
              @click="savePhishing"
          >
            ذخیره عبارت
          </AppButton>

          <AppButton
              variant="secondary"
              :disabled="phishingLoading"
              @click="
              phishingOpen = false
            "
          >
            انصراف
          </AppButton>
        </template>

        <template v-else>
          <AppButton
              block
              variant="danger"
              :loading="phishingLoading"
              @click="removePhishing"
          >
            حذف کد
          </AppButton>
        </template>
      </template>
    </AppModal>

    <AppModal
        :model-value="
        Boolean(confirmation)
      "
        :title="
        confirmationCopy.title
      "
        :description="
        confirmationCopy.description
      "
        size="sm"
        :dismissible="!confirming"
        @update:model-value="
        (value) => {
          if (!value && !confirming) {
            closeConfirmation()
          }
        }
      "
    >
      <div
          class="confirmation-visual"
      >
        <span>
          <AppIcon
              name="warning"
              :size="25"
          />
        </span>

        <div
            class="confirmation-copy"
        >
          <p>
            این عملیات فوراً روی امنیت حساب اعمال می‌شود.
          </p>

          <small
              v-if="
              confirmation?.kind ===
              'disable-2fa'
            "
          >
            پس از غیرفعال‌سازی، کلید جدیدی ساخته
            می‌شود؛ برای فعال‌سازی مجدد، QR جدید را
            دوباره اسکن کنید.
          </small>

        </div>
      </div>

      <div
          v-if="
          confirmation?.kind ===
          'disable-2fa'
        "
          class="disable-2fa-form"
      >
        <AppInput
            :model-value="
            disableTwoFactorCode
          "
            label="کد برنامه Authenticator"
            inputmode="numeric"
            autocomplete="one-time-code"
            maxlength="6"
            ltr
            placeholder="••••••"
            :error="
            disableTwoFactorError
          "
            @update:model-value="
            updateDisableTwoFactorCode
          "
        />

        <p
            class="disable-2fa-help"
        >
          برای غیرفعال‌کردن ورود دومرحله‌ای،
          کد ۶ رقمی فعلی برنامه Authenticator
          را وارد کنید.
        </p>
      </div>

      <template #footer>
        <AppButton
            variant="danger"
            block
            :loading="
            confirming
          "
            @click="runConfirmation"
        >
          {{
            confirmationCopy.confirm
          }}
        </AppButton>

        <AppButton
            variant="secondary"
            :disabled="confirming"
            @click="
            closeConfirmation
          "
        >
          انصراف
        </AppButton>
      </template>
    </AppModal>
  </div>
</template>

<style scoped>
.security-page {
  display: grid;
  align-content: start;
  gap: var(--space-5);
}

.security-page :deep(.page-header) {
  margin-bottom: 0;
}

.notice {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border: 1px solid;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
}

.notice span {
  flex: 1;
}

.notice button {
  display: inline-grid;
  min-width: 2.75rem;
  min-height: 2.75rem;
  padding-inline: var(--space-2);
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: inherit;
  font-weight: 600;
  place-items: center;
}

.notice button:focus-visible {
  outline: 2px solid currentColor;
  outline-offset: 2px;
}

.notice.success {
  border-color: rgba(53, 201, 149, .23);
  background: var(--color-success-soft);
  color: var(--color-success);
}

.notice.danger {
  border-color: rgba(240, 108, 117, .23);
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.score-skeleton {
  display: flex;
  align-items: center;
  gap: var(--space-5);
}

.score-skeleton > div {
  display: grid;
  grid-template-columns:
    minmax(0, 1fr);
  min-width: 0;
  flex: 1;
  gap: var(--space-3);
}

.score-skeleton :deep(.skeleton) {
  max-width: 100%;
}

.score-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-6);
  overflow: hidden;
  background: linear-gradient(
      120deg,
      var(--color-surface-1),
      var(--color-primary-soft)
  );
}

.score-card::after {
  position: absolute;
  inset-block: 16%;
  inset-inline-start: 0;
  width: 2px;
  border-radius: var(--radius-pill);
  background: linear-gradient(
      180deg,
      transparent,
      var(--score-color),
      transparent
  );
  content: '';
  opacity: .8;
}

.score-card > * {
  position: relative;
  z-index: 1;
}

.score-ring {
  position: relative;
  display: grid;
  width: 7.5rem;
  height: 7.5rem;
  flex: 0 0 auto;
  border-radius: 50%;
  background: conic-gradient(
      var(--score-color) var(--score-angle),
      var(--color-surface-3) 0
  );
  place-items: center;
}

.score-ring::before {
  position: absolute;
  inset: .5rem;
  border-radius: 50%;
  background: var(--color-surface-1);
  content: '';
}

.score-ring span {
  position: relative;
  display: grid;
  text-align: center;
}

.score-ring strong {
  font-size: var(--font-size-2xl);
}

.score-ring small {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.score-strong {
  --score-color: var(--color-success);
}

.score-medium {
  --score-color: var(--color-warning);
}

.score-weak {
  --score-color: var(--color-danger);
}

.score-copy {
  min-width: 0;
  flex: 1;
}

.score-copy > span {
  color: var(--score-color);
  font-size: var(--font-size-xs);
  font-weight: 600;
}

.score-copy h2 {
  margin: .15rem 0;
  font-size: var(--font-size-2xl);
}

.score-copy p {
  max-width: 35rem;
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.score-facts {
  display: grid;
  grid-template-columns:
    repeat(3, 1fr);
  gap: var(--space-2);
}

.score-facts > div {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 8.5rem;
  padding: var(--space-3);
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-md);
  background: var(--color-surface-2);
  color: var(--color-primary);
}

.score-facts span {
  display: grid;
  color: var(--color-text-primary);
}

.score-facts small {
  color: var(--color-text-muted);
  font-size: .66rem;
}

.score-facts strong {
  font-size: var(--font-size-xs);
}

.security-grid {
  display: grid;
  grid-template-columns:
    minmax(0, 1.25fr)
    minmax(20rem, .75fr);
  grid-template-areas:
    "protection withdrawal"
    "events withdrawal";
  align-items: start;
  gap: var(--space-5);
}

.protection-card {
  grid-area: protection;
}

.withdrawal-security {
  grid-area: withdrawal;
}

.events-card {
  grid-area: events;
}

.section-heading {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.section-heading > span {
  display: grid;
  width: 2.75rem;
  height: 2.75rem;
  flex: 0 0 auto;
  border-radius: .85rem;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  place-items: center;
}

.section-heading h2 {
  margin: 0;
  font-size: var(--font-size-lg);
}

.section-heading p {
  margin: .1rem 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.setting-list {
  display: grid;
}

.setting-row {
  display: grid;
  grid-template-columns:
    auto
    minmax(0, 1fr)
    auto
    auto;
  align-items: center;
  gap: var(--space-3);
  padding-block: var(--space-4);
}

.setting-row + .setting-row {
  border-top: 1px solid var(--color-border-soft);
}

.setting-row.featured {
  margin-inline: calc(
      var(--space-2) * -1
  );
  padding-inline: var(--space-2);
  border-radius: var(--radius-md);
  background: linear-gradient(
      90deg,
      var(--color-primary-soft),
      transparent
  );
}

.setting-icon {
  display: grid;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: .85rem;
  background: var(--color-surface-2);
  color: var(--color-text-secondary);
  place-items: center;
}

.setting-row.featured
.setting-icon {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.setting-row > div {
  display: grid;
}

.setting-row small,
.row-note {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.withdrawal-security {
  display: grid;
  gap: var(--space-4);
}

.feature-block {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-lg);
  background: var(--color-surface-2);
  transition: background var(--transition-fast),
  border-color var(--transition-fast);
}

.feature-title {
  display: grid;
  grid-template-columns:
    auto 1fr;
  align-items: start;
  gap: var(--space-3);
}

.feature-title > span {
  display: grid;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: .75rem;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  place-items: center;
}

.feature-title > div {
  display: grid;
  gap: .12rem;
}

.feature-title small {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.feature-header {
  display: grid;
  grid-template-columns: 1fr;
  align-items: start;
  gap: var(--space-2);
}

.feature-header :deep(.app-switch) {
  justify-self: start;
}

.phishing-feature {
  display: grid;
  gap: var(--space-3);
}

.phishing-feature
.feature-title {
  grid-template-columns:
    auto minmax(0, 1fr);
  align-items: center;
}

.phishing-status-row {
  display: flex;
  align-items: center;
  justify-content: center;
}

.phishing-action {
  justify-self: center;
  min-width: 10rem;
}

.whitelist-feature {
  gap: var(--space-4);
}

.whitelist-description {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-primary-soft);
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  line-height: 1.8;
}

.whitelist-description
:deep(svg) {
  flex: 0 0 auto;
  color: var(--color-primary);
}

.address-management-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.address-management-header > div {
  display: grid;
  gap: .15rem;
}

.address-management-header strong {
  font-size: var(--font-size-sm);
}

.address-management-header small {
  color: var(--color-text-muted);
  font-size: .7rem;
}

.withdrawal-address-list {
  display: grid;
  max-height: 18rem;
  overflow-y: auto;
  border-top: 1px solid var(--color-border-soft);
  border-bottom: 1px solid var(--color-border-soft);
  scrollbar-width: thin;
  scrollbar-color: var(--color-border-hover) transparent;
}

.withdrawal-address-list::-webkit-scrollbar {
  width: .35rem;
}

.withdrawal-address-list::-webkit-scrollbar-track {
  background: transparent;
}

.withdrawal-address-list::-webkit-scrollbar-thumb {
  border-radius: var(--radius-pill);
  background: var(--color-border-hover);
}

.withdrawal-address-link {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  min-width: 0;
  padding: .72rem .2rem;
  border: 0;
  border-bottom: 1px solid var(--color-border-soft);
  background: transparent;
  color: var(--color-text-primary);
  text-align: start;
  cursor: pointer;
  transition: background var(--transition-fast),
  color var(--transition-fast);
}

.withdrawal-address-link:last-child {
  border-bottom: 0;
}

.withdrawal-address-link:hover {
  background: color-mix(
      in srgb,
      var(--color-primary-soft) 35%,
      transparent
  );
}

.withdrawal-address-link:focus-visible {
  outline: 2px solid var(--color-border-focus);
  outline-offset: -2px;
  border-radius: var(--radius-sm);
}

.withdrawal-address-link.is-default {
  color: var(--color-primary);
}

.withdrawal-address-link__icon {
  display: grid;
  width: 2rem;
  height: 2rem;
  flex: 0 0 auto;
  border-radius: .65rem;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  place-items: center;
}

.withdrawal-address-link__copy {
  min-width: 0;
  flex: 1;
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.withdrawal-address-link__default {
  flex: 0 0 auto;
  padding: .22rem .5rem;
  border-radius: var(--radius-pill);
  background: var(--color-gold-soft);
  color: var(--color-gold);
  font-size: .63rem;
  font-weight: 700;
}

.address-loading {
  display: grid;
  gap: var(--space-2);
}

.withdrawal-address-details {
  display: grid;
  gap: var(--space-3);
}

.withdrawal-address-detail-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-border-soft);
}

.withdrawal-address-detail-row span,
.withdrawal-address-detail-block > span,
.withdrawal-address-detail-status span {
  color: var(--color-text-muted);
  font-size: .7rem;
}

.withdrawal-address-detail-row strong {
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  text-align: end;
}

.withdrawal-address-detail-block {
  display: grid;
  gap: .25rem;
  min-width: 0;
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-surface-2);
}

.withdrawal-address-detail-block bdi {
  overflow-wrap: anywhere;
  color: var(--color-text-secondary);
  font-family: ui-monospace, monospace;
  font-size: .72rem;
  line-height: 1.7;
}

.withdrawal-address-detail-status {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-2);
}

.withdrawal-address-detail-status > div {
  display: grid;
  gap: .3rem;
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-surface-2);
}

.withdrawal-address-detail-status strong {
  font-size: var(--font-size-xs);
}

.withdrawal-address-detail-note {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-info-soft);
  color: var(--color-info);
  font-size: var(--font-size-xs);
}

.withdrawal-address-detail-default {
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-gold-soft);
  color: var(--color-gold);
  font-size: var(--font-size-xs);
  font-weight: 700;
  text-align: center;
}

.address-create-network
span {
  color: var(--color-text-muted);
  font-size: .7rem;
}

.address-create-network
strong {
  font-size: var(--font-size-sm);
}

.address-create-network
small {
  color: var(--color-text-muted);
  font-size: .7rem;
  line-height: 1.7;
}

.address-create-hint {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-primary-soft);
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  line-height: 1.8;
}

.address-create-hint
:deep(svg) {
  flex: 0 0 auto;
  color: var(--color-primary);
}

.address-confirmation-step {
  display: grid;
  gap: var(--space-4);
}

.review-address {
  display: grid;
  gap: .2rem;
  min-width: 0;
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-surface-2);
}

.review-address span {
  color: var(--color-text-muted);
  font-size: .7rem;
}

.review-address bdi {
  overflow-wrap: anywhere;
  color: var(--color-text-secondary);
  font-family: ui-monospace, monospace;
  font-size: var(--font-size-xs);
}

.review-address small {
  color: var(--color-text-muted);
  font-size: .68rem;
}

.security-message {
  margin: 0;
  color: var(--color-success);
  font-size: var(--font-size-xs);
}

.challenge-expiry {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  text-align: center;
}

.challenge-expiry.expired {
  color: var(--color-danger);
}

.modal-form {
  display: grid;
  gap: var(--space-4);
}

.modal-error {
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-danger-soft);
  color: var(--color-danger);
  font-size: var(--font-size-sm);
  line-height: 1.7;
}

.sessions-card {
  overflow: hidden;
}

.events-card {
  overflow: hidden;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-5);
  border-bottom: 1px solid var(--color-border-soft);
}

.list-header > div {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.list-header > div > span {
  display: grid;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: .85rem;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  place-items: center;
}

.list-header h2 {
  margin: 0;
  font-size: var(--font-size-lg);
}

.list-header p {
  margin: .1rem 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.session-list {
  display: grid;
}

.session-row {
  display: grid;
  grid-template-columns:
    auto
    minmax(0, 1fr)
    auto
    auto;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-5);
}

.session-row + .session-row {
  border-top: 1px solid var(--color-border-soft);
}

.session-row.current {
  background: linear-gradient(
      90deg,
      var(--color-success-soft),
      transparent 55%
  );
}

.device-icon {
  display: grid;
  width: 3rem;
  height: 3rem;
  border-radius: 1rem;
  background: var(--color-surface-2);
  color: var(--color-text-secondary);
  place-items: center;
}

.current .device-icon {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.session-copy {
  min-width: 0;
}

.session-copy > div {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.session-device-line {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
}

.session-device-line h3 {
  margin: 0;
  font-size: var(--font-size-md);
}

.session-copy > span {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text-muted);
  font-size: .68rem;
}

.session-copy > span i {
  width: .25rem;
  height: .25rem;
  border-radius: 50%;
  background: var(--color-border-hover);
}

.session-time {
  display: grid;
  min-width: 8rem;
  text-align: end;
}

.session-time small {
  color: var(--color-text-muted);
  font-size: .68rem;
}

.session-time strong {
  font-size: var(--font-size-xs);
}

.withdrawal-modal-actions {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(6rem, .55fr);
  gap: var(--space-3);
  width: 100%;
}

.withdrawal-modal-actions :deep(.app-button) {
  width: 100%;
  min-width: 0;
}

@media (max-width: 420px) {
  .withdrawal-modal-actions {
    grid-template-columns: 1fr;
  }
}


.event-list {
  display: grid;
  max-height: 30.8rem;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-width: thin;
  scrollbar-color: var(--color-border-hover) transparent;
  scroll-snap-type: y proximity;
}

.event-list article {
  display: grid;
  grid-template-columns:
    auto
    minmax(0, 1fr)
    auto;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  scroll-snap-align: start;
}

.event-list article + article {
  border-top: 1px solid var(--color-border-soft);
}

.event-list::-webkit-scrollbar {
  width: .4rem;
}

.event-list::-webkit-scrollbar-track {
  background: transparent;
}

.event-list::-webkit-scrollbar-thumb {
  border-radius: var(--radius-pill);
  background: var(--color-border-hover);
}

.event-list h3 {
  margin: 0;
  font-size: var(--font-size-sm);
}

.event-list p {
  margin: .05rem 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
}

.event-list small {
  color: var(--color-text-muted);
  font-size: .68rem;
}

.event-time {
  display: grid;
  justify-items: end;
  gap: .15rem;
  min-width: max-content;
}

.event-time strong {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.event-time small {
  color: var(--color-text-muted);
  font-size: .66rem;
  white-space: nowrap;
  opacity: .8;
}

.event-icon {
  display: grid;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: .85rem;
  place-items: center;
}

.event-list article:hover,
.setting-row:hover {
  background: color-mix(
      in srgb,
      var(--color-primary-soft) 45%,
      transparent
  );
}

.two-factor-setup {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-4);
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-lg);
  background: var(--color-surface-2);
}

.two-factor-qr {
  display: grid;
  justify-items: center;
  width: 100%;
  padding-top: var(--space-1);
}

.two-factor-manual {
  display: grid;
  gap: var(--space-2);
  width: 100%;
  min-width: 0;
}

.two-factor-manual
> strong {
  font-size: var(--font-size-sm);
}

.two-factor-manual p {
  margin: 0 0 var(--space-2);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  line-height: 1.8;
}

.setup-secret {
  display: flex;
  min-width: 0;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  width: 100%;
  padding: var(--space-2);
  box-sizing: border-box;
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface-3);
}

.setup-secret bdi {
  min-width: 0;
  overflow: hidden;
  direction: ltr;
  font-size: var(--font-size-xs);
  font-weight: 700;
  letter-spacing: .04em;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.two-factor-actions {
  display: grid;
  grid-template-columns:
    minmax(0, 1fr)
    minmax(0, 1fr);
  gap: var(--space-3);
  width: 100%;
}

.two-factor-actions
:deep(.app-button) {
  width: 100%;
  min-width: 0;
}

.auth-guide {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-primary-soft);
}

.auth-guide > span {
  display: grid;
  width: 3rem;
  height: 3rem;
  flex: 0 0 auto;
  border-radius: .9rem;
  background: var(--color-surface-2);
  color: var(--color-primary);
  place-items: center;
}

.auth-guide p {
  margin: .1rem 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.phishing-help {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-warning-soft);
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
}

.phishing-help svg {
  color: var(--color-warning);
}

.confirmation-visual {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-danger-soft);
}

.confirmation-visual > span {
  display: grid;
  width: 2.75rem;
  height: 2.75rem;
  flex: 0 0 auto;
  border-radius: .8rem;
  background: rgba(
      240,
      108,
      117,
      .12
  );
  color: var(--color-danger);
  place-items: center;
}

.confirmation-visual p {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.confirmation-copy {
  display: grid;
  min-width: 0;
  gap: var(--space-1);
}

.confirmation-copy small {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  line-height: 1.8;
}

.confirmation-address {
  display: grid;
  gap: .2rem;
  margin-top: var(--space-4);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-surface-2);
}

.confirmation-address span {
  color: var(--color-text-muted);
  font-size: .7rem;
}

.confirmation-address bdi {
  overflow-wrap: anywhere;
  color: var(--color-text-secondary);
  font-family: ui-monospace, monospace;
  font-size: var(--font-size-xs);
}

.confirmation-address small {
  color: var(--color-text-muted);
  font-size: .68rem;
}

.disable-2fa-form {
  display: grid;
  gap: var(--space-2);
  margin-top: var(--space-4);
}

.disable-2fa-help {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  line-height: 1.8;
}

@media (max-width: 1150px) {
  .score-card {
    flex-wrap: wrap;
  }

  .score-facts {
    width: 100%;
  }

  .security-grid {
    grid-template-columns: 1fr;
    grid-template-areas:
      "protection"
      "withdrawal"
      "events";
  }
}

@media (max-width: 767px) {
  .score-card {
    align-items: flex-start;
    gap: var(--space-4);
  }

  .score-ring {
    width: 5.5rem;
    height: 5.5rem;
  }

  .score-copy {
    width: calc(
        100% - 7rem
    );
  }

  .score-copy h2 {
    font-size: var(--font-size-xl);
  }

  .score-copy p {
    display: none;
  }

  .score-facts {
    grid-template-columns: 1fr;
  }

  .score-facts > div {
    min-width: 0;
  }

  .setting-row {
    grid-template-columns:
      auto
      minmax(0, 1fr)
      auto;
  }

  .setting-row
  > :deep(.status) {
    display: none;
  }

  .setting-row
  :deep(.app-button),
  .setting-row .row-note {
    grid-column: 2 / -1;
    justify-self: start;
  }

  .setting-row
  :deep(.app-button) {
    min-height: 2.75rem;
  }

  .feature-header {
    grid-template-columns: 1fr;
  }

  .feature-header
  :deep(.app-switch) {
    width: auto;
  }

  .address-management-header {
    align-items: center;
  }

  .withdrawal-address-list {
    max-height: 16rem;
  }

  .withdrawal-address-detail-status {
    grid-template-columns: 1fr;
  }

  .list-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .list-header
  :deep(.app-button) {
    width: 100%;
    min-height: 2.75rem;
  }

  .session-row {
    grid-template-columns:
      auto
      minmax(0, 1fr);
    gap: var(--space-3);
    padding: var(--space-4);
  }

  .session-time {
    grid-column: 2;
    min-width: 0;
    text-align: start;
  }

  .session-row
  :deep(.app-button) {
    grid-column: 2;
    justify-self: start;
    min-height: 2.75rem;
  }

  .event-list {
    max-height: 20rem;
  }

  .event-list article {
    grid-template-columns:
      auto
      minmax(0, 1fr);
    gap: var(--space-3);
    padding: var(--space-4);
  }

  .event-list time {
    grid-column: 2;
    justify-items: start;
  }

  .event-list p {
    line-height: 1.8;
  }

  .confirmation-visual {
    align-items: flex-start;
  }

  .confirmation-copy {
    flex: 1;
  }
}

@media (max-width: 399px) {
  .score-ring {
    width: 4.75rem;
    height: 4.75rem;
  }

  .score-ring strong {
    font-size: var(--font-size-xl);
  }

  .score-copy {
    width: calc(
        100% - 5.75rem
    );
  }

  .score-copy h2 {
    font-size: var(--font-size-lg);
  }

  .setting-row {
    grid-template-columns:
      auto
      minmax(0, 1fr);
  }

  .setting-row
  > :deep(.status) {
    display: inline-flex;
    grid-column: 2;
    justify-self: start;
  }

  .setting-row
  :deep(.app-button),
  .setting-row .row-note {
    grid-column: 1 / -1;
    width: 100%;
  }

  .feature-title {
    grid-template-columns:
      auto 1fr;
  }

  .withdrawal-address-link {
    padding-block: .65rem;
  }

  .two-factor-actions {
    grid-template-columns: 1fr;
  }
}
</style>