"use client"

import { useCartStore } from "../store/cartStore"

export default function BuyButton({ product }: any) {
  const addItem = useCartStore(s => s.addItem)

  if (product.stock > 0)
    return (
      <button
        onClick={() => addItem(product)}
        className="bg-violet-700 text-violet-50 px-6 py-3 rounded-xl"
      >
        Add to Cart
      </button>
    )

  if (product.preorder === "TRUE")
    return (
      <button className="bg-amber-600 text-amber-50 px-6 py-3 rounded-xl">
        Preorder
      </button>
    )

  return <div className="text-red-700 font-medium">Out of stock</div>
}