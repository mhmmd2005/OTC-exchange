const translations = {
    'Invalid OTP.':
        'کد تأیید صحیح نیست.',

    'Invalid verification challenge.':
        'درخواست تأیید معتبر نیست. لطفاً دوباره کد درخواست کنید.',

    'This OTP challenge has already been used.':
        'این کد تأیید قبلاً استفاده شده است.',

    'OTP has expired. Please request a new one.':
        'کد تأیید منقضی شده است. لطفاً یک کد جدید درخواست کنید.',

    'OTP verification limit reached. Please request a new one.':
        'تعداد تلاش‌های تأیید کد به پایان رسیده است. لطفاً یک کد جدید درخواست کنید.',

    'Please wait before requesting a new OTP.':
        'لطفاً قبل از درخواست کد جدید کمی صبر کنید.',

    'Too many OTP requests. Please try again later.':
        'تعداد درخواست‌های کد بیش از حد مجاز است. لطفاً بعداً دوباره تلاش کنید.',

    'Invalid credentials.':
        'اطلاعات ورود صحیح نیست.',

    'Too many failed login attempts. Please try later.':
        'تعداد تلاش‌های ناموفق ورود بیش از حد مجاز است. لطفاً بعداً دوباره تلاش کنید.',

    'Invalid or expired flow token.':
        'جلسه احراز هویت منقضی شده است. لطفاً دوباره شروع کنید.',

    'Invalid flow token.':
        'جلسه احراز هویت معتبر نیست.',

    'Flow validation failed.':
        'اعتبارسنجی جلسه احراز هویت ناموفق بود.',

    'OTP validation is required before proceeding.':
        'ابتدا باید کد تأیید را وارد و تأیید کنید.',

    'This phone number is already registered.':
        'این شماره موبایل قبلاً ثبت شده است.',

    'This phone number already has an account.':
        'این شماره موبایل قبلاً دارای حساب کاربری است.',

    'Passwords do not match.':
        'رمزهای عبور یکسان نیستند.',

    'Refresh token is required.':
        'توکن ورود الزامی است.',

    'Invalid refresh token.':
        'توکن ورود معتبر نیست.',

    'Logged out successfully.':
        'با موفقیت خارج شدید.',

    'This field is required.':
        'این فیلد الزامی است.',

    'Enter a valid value.':
        'مقدار واردشده معتبر نیست.',

    'Ensure this field has at least 6 characters.':
        'این فیلد باید حداقل ۶ کاراکتر داشته باشد.',

    'Ensure this field has no more than 6 characters.':
        'این فیلد نباید بیشتر از ۶ کاراکتر باشد.',

    'Ensure this field has no more than 20 characters.':
        'این فیلد نباید بیشتر از ۲۰ کاراکتر باشد.',
}

export function translateError(message, fallback = 'خطایی رخ داد.') {
    if (!message) {
        return fallback
    }

    const normalizedMessage = String(message).trim()

    if (
        normalizedMessage.startsWith(
            'Too many OTP requests from this IP.'
        )
    ) {
        const secondsMatch = normalizedMessage.match(
            /Expected available in (\d+) seconds?\./i
        )

        if (secondsMatch) {
            const seconds = Number(secondsMatch[1])

            return `به دلیل تعداد زیاد درخواست، لطفاً ${seconds} ثانیه دیگر دوباره تلاش کنید.`
        }

        return 'تعداد درخواست‌های کد از این IP بیش از حد مجاز است. لطفاً بعداً دوباره تلاش کنید.'
    }

    return translations[normalizedMessage] || normalizedMessage
}

export default translateError