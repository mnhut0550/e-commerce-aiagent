"use client"

import { useCartStore } from "./cartStore"
import Container from "@/components/ui/Container"
import { useState } from "react"

export default function CartPage() {
  const { items, removeItem, updateQuantity } = useCartStore()

  const total = items.reduce((sum, i) => sum + i.price * i.quantity, 0)

  const [form, setForm] = useState({
    name: "", phone: "", email: "", note: ""
  })

  const handleOrder = async () => {
    console.log("order:", { items, form })
  }

  if (items.length === 0)
    return (
      <Container>
        <div className="py-40 text-center text-gray-400 text-lg">
          Giỏ hàng trống
        </div>
      </Container>
    )

  return (
    <Container>
      <div className="py-20 grid grid-cols-1 lg:grid-cols-3 gap-12">

        {/* Danh sách sản phẩm */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-2xl font-semibold text-white mb-6">Giỏ hàng</h2>
          {items.map(item => (
            <div key={item.id} className="flex gap-4 bg-zinc-900 rounded-2xl p-4">
              <img src={item.image_url} className="w-24 h-24 object-cover rounded-xl" />
              <div className="flex-1 space-y-2">
                <p className="text-white font-medium">{item.name}</p>
                <p className="text-gray-400">{item.price.toLocaleString("vi-VN")} ₫</p>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => updateQuantity(item.id, item.quantity - 1)}
                    className="w-7 h-7 rounded-full bg-zinc-700 text-white"
                  >−</button>
                  <span className="text-white">{item.quantity}</span>
                  <button
                    onClick={() => updateQuantity(item.id, item.quantity + 1)}
                    className="w-7 h-7 rounded-full bg-zinc-700 text-white"
                  >+</button>
                </div>
              </div>
              <button
                onClick={() => removeItem(item.id)}
                className="text-red-500 text-sm self-start"
              >Xóa</button>
            </div>
          ))}
        </div>

        {/* Form checkout */}
        <div className="bg-zinc-900 rounded-2xl p-6 space-y-4 h-fit">
          <h2 className="text-xl font-semibold text-white">Thông tin đặt hàng</h2>

          {[
            { key: "name", placeholder: "Họ tên" },
            { key: "phone", placeholder: "Số điện thoại" },
            { key: "email", placeholder: "Email" },
          ].map(({ key, placeholder }) => (
            <input
              key={key}
              placeholder={placeholder}
              value={form[key as keyof typeof form]}
              onChange={e => setForm({ ...form, [key]: e.target.value })}
              className="w-full bg-zinc-800 text-white rounded-xl px-4 py-3 outline-none placeholder:text-gray-500"
            />
          ))}

          <textarea
            placeholder="Ghi chú"
            value={form.note}
            onChange={e => setForm({ ...form, note: e.target.value })}
            className="w-full bg-zinc-800 text-white rounded-xl px-4 py-3 outline-none placeholder:text-gray-500 resize-none h-24"
          />

          <div className="flex justify-between text-white font-semibold text-lg pt-2">
            <span>Tổng</span>
            <span>{total.toLocaleString("vi-VN")} ₫</span>
          </div>

          <button
            onClick={handleOrder}
            className="w-full bg-violet-700 text-white py-3 rounded-xl font-medium"
          >
            Đặt hàng
          </button>
        </div>

      </div>
    </Container>
  )
}