"use client"

import { motion } from "framer-motion"

export default function HeroProduct() {

  return (

    <section className="bg-gray-50 py-28 text-center">

      <motion.h1
        initial={{ opacity:0, y:20 }}
        animate={{ opacity:1, y:0 }}
        transition={{ duration:0.6 }}
        className="text-6xl font-semibold"
      >
        AI Technology Products
      </motion.h1>

      <p className="text-gray-500 mt-4 text-lg">
        Smart devices and AI edge computing
      </p>

      <div className="mt-16 flex justify-center">

        <img
          src="https://picsum.photos/900/500"
          className="rounded-3xl shadow-lg"
        />

      </div>

    </section>

  )
}