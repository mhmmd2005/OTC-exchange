export function getPasswordRequirements(password = '') {
  return [
    {
      key: 'length',
      label: 'حداقل ۸ کاراکتر',
      valid: password.length >= 8,
    },
    {
      key: 'uppercase',
      label: 'یک حرف بزرگ انگلیسی',
      valid: /[A-Z]/.test(password),
    },
    {
      key: 'lowercase',
      label: 'یک حرف کوچک انگلیسی',
      valid: /[a-z]/.test(password),
    },
    {
      key: 'number',
      label: 'یک عدد',
      valid: /\d/.test(password),
    },
    {
      key: 'special',
      label: 'یک کاراکتر خاص',
      valid: /[^A-Za-z0-9]/.test(password),
    },
  ]
}

export function validatePassword(password = '') {
  const requirements = getPasswordRequirements(password)
  return requirements.every((item) => item.valid)
}
