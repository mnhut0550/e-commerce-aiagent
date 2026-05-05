import { getProduct } from "@/lib/api"
import Container from "@/components/ui/Container"
import ProductGallery from "@/components/product/ProductGallery"
import ProductInfo from "@/components/product/ProductInfo"
import { notFound } from "next/navigation"

export default async function ProductPage({ params }: any) {

  const { id } = await params

  const product = await getProduct(id)

  if (!product) return notFound()

  const images = product.image_url
    ? product.image_url.split(",")
    : []

  return (
    <Container>
      <div className="grid md:grid-cols-2 gap-12 py-20">
        <ProductGallery images={images} />
        <ProductInfo product={product} />
      </div>
    </Container>
  )
}