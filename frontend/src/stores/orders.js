import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ordersService } from '../services/orders'

export const useOrdersStore = defineStore('orders', () => {
  const orders = ref([])
  const transactions = ref([])
  const loading = ref(false)

  async function fetchOrders() {
    loading.value = true
    try {
      const response = await ordersService.getOrders()
      orders.value = response.data
    } finally {
      loading.value = false
    }
  }

  async function fetchTransactions() {
    const response = await ordersService.getTransactions()
    transactions.value = response.data
  }

  async function createOrder(payload) {
    const response = await ordersService.createOrder(payload)
    return response.data
  }

  return { orders, transactions, loading, fetchOrders, fetchTransactions, createOrder }
})
