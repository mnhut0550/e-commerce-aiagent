import { getProducts } from "@/lib/api"
import Container from "@/components/ui/Container"
import ProductGrid from "@/components/product/ProductGrid"
import { Filters } from "@/components/search_filters/ProductFilters"
import { Suspense } from "react"

export default async function Page({ searchParams }: any) {
  const { category, subcategory } = await searchParams
  const products = await getProducts(category, subcategory)

  return (
    <Container>
      <div className="py-20">
        <Suspense fallback={null}>
          <Filters />
        </Suspense>
        <ProductGrid 
          key={`${category}-${subcategory}`} 
          products={products} 
        />
      </div>
    </Container>
  )
}