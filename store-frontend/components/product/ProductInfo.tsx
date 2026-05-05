import BuyButton from "./BuyButton"

export default function ProductInfo({ product }: any) {

  const price = Number(product?.price || 0)

  return (

    <div className="space-y-6">

      {/* Product name */}
      <h1 className="text-4xl font-semibold text-white">
        {product?.name}
      </h1>

      {/* Description */}
      <p className="text-gray-300 text-lg leading-relaxed max-w-xl">
        {product?.full_desc}
      </p>

      {/* Price */}
      <div className="flex items-end gap-2">

        <span className="text-3xl font-bold text-white">
          {price.toLocaleString("vi-VN")}
        </span>

        <span className="text-xl text-gray-400">
          ₫
        </span>

      </div>

      {/* Buy button */}
      <div className="pt-2">
        <BuyButton product={product}/>
      </div>

    </div>

  )
}