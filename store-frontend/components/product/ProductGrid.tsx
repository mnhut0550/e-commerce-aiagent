"use client"

import { useState } from "react"
import ProductCard from "./ProductCard"
import ProductSearch from "../search_filters/ProductSearch"

export default function ProductGrid({ products, initialQ }: any) {

  const [filtered, setFiltered] = useState(
    initialQ
      ? products.filter((p: any) =>
          p.name.toLowerCase().includes(initialQ.toLowerCase())
        )
      : products
  )

  return (
    <div>
      <ProductSearch products={products} onFilter={setFiltered} initialQ={initialQ} />
      <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
        {filtered.map((p: any) => (
          <ProductCard key={p.id} product={p} />
        ))}
      </div>
    </div>
  )
}