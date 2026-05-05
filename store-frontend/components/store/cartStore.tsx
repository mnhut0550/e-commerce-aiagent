import { create } from "zustand"
import { persist } from "zustand/middleware"

export type CartItem = {
  id: string
  name: string
  price: number
  image_url: string
  quantity: number
}

type CartStore = {
  items: CartItem[]
  addItem: (product: any) => void
  removeItem: (id: string) => void
  updateQuantity: (id: string, quantity: number) => void
  clear: () => void
}

export const useCartStore = create<CartStore>()(
  persist(
    (set, get) => ({
      items: [],

      addItem: (product) => {
        const existing = get().items.find(i => i.id === product.id)
        if (existing) {
          set({ items: get().items.map(i =>
            i.id === product.id ? { ...i, quantity: i.quantity + 1 } : i
          )})
        } else {
          set({ items: [...get().items, {
            id: product.id,
            name: product.name,
            price: Number(product.price),
            image_url: product.image_url,
            quantity: 1
          }]})
        }
      },

      removeItem: (id) =>
        set({ items: get().items.filter(i => i.id !== id) }),

      updateQuantity: (id, quantity) => {
        if (quantity < 1) return
        set({ items: get().items.map(i =>
          i.id === id ? { ...i, quantity } : i
        )})
      },

      clear: () => set({ items: [] })
    }),
    { name: "cart" }
  )
)