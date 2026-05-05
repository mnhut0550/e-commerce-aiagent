"use client"

import Link from "next/link"
import { useCartStore } from "../store/cartStore"
import { ShoppingCart } from "lucide-react"

export default function Navbar() {
  const items = useCartStore(s => s.items)
  const count = items.reduce((sum, i) => sum + i.quantity, 0)

  return (
    <header className="sticky top-0 backdrop-blur bg-white/70 z-50 border-b">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">

        <div className="font-semibold text-lg text-blue-600">
          <a href="/">TechStore</a>
        </div>

        <nav className="flex items-center gap-6 text-sm text-gray-700">
          <Link href="/cart" className="relative">
            <ShoppingCart size={20} />
            {count > 0 && (
              <span className="absolute -top-2 -right-2 bg-violet-600 text-white text-xs w-4 h-4 rounded-full flex items-center justify-center">
                {count}
              </span>
            )}
          </Link>
        </nav>

      </div>
    </header>
  )
}