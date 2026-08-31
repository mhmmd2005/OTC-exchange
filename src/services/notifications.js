export const notificationsService = {
  async getNotifications() {
    return {
      data: [
        { id: 1, title: 'سفارش جدید', message: 'سفارش OTC-24082 ثبت شد و در انتظار بررسی است.', status: 'unread', type: 'order', time: '۲ دقیقه پیش' },
        { id: 2, title: 'احراز هویت', message: 'مدارک شما در حال بررسی است.', status: 'read', type: 'kyc', time: '۱ ساعت پیش' },
        { id: 3, title: 'امنیت', message: 'دستگاه جدید در تهران وارد شد.', status: 'unread', type: 'security', time: '۳ ساعت پیش' },
      ]
    }
  },
}

export default notificationsService
