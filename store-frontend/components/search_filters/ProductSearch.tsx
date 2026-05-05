"use client"

import { useState } from "react"

export default function ProductSearch({ products, onFilter, initialQ = "" }: any) {

  const [q, setQ] = useState(initialQ)

  function handleSearch(value: string) {
    setQ(value)
    const filtered = products.filter((p: any) =>
      p.name.toLowerCase().includes(value.toLowerCase())
    )
    onFilter(filtered)
  }

  return (
    <input
      value={q}
      onChange={(e) => handleSearch(e.target.value)}
      placeholder="Search by name..."
      className="w-full border rounded-xl px-4 py-3"
    />
  )
}