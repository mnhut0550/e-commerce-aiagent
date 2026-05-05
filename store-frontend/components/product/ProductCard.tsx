"use client"

import Link from "next/link"
import { motion } from "framer-motion"

export default function ProductCard({product}:any){

  const price = Number(product?.price || 0)

  return(

    <Link href={`/products/${product.id}`}>

      <motion.div
        whileHover={{y:-6}}
        className="bg-zinc-900 rounded-3xl p-6 hover:shadow-xl hover:bg-zinc-800 transition"
      >

        <img
          src={product.image_url}
          className="w-full h-48 object-cover rounded-xl"
        />

        <h3 className="mt-4 font-semibold text-lg text-white">
          {product.name}
        </h3>

        <p className="text-gray-400 text-sm mt-2">
          {product.short_desc}
        </p>

        <div className="mt-4 font-bold text-white">
          {price.toLocaleString("vi-VN")} ₫
        </div>

      </motion.div>

    </Link>

  )
}