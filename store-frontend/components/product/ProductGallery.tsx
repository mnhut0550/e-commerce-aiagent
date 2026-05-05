"use client"

import useEmblaCarousel from "embla-carousel-react"

export default function ProductGallery({images}:any){

  const [ref] = useEmblaCarousel()

  return(

    <div ref={ref} className="overflow-hidden rounded-3xl">

      <div className="flex">

        {images.map((img:string,i:number)=>(
          <div key={i} className="flex-[0_0_100%]">
            <img src={img} className="w-full h-[420px] object-cover"/>
          </div>
        ))}

      </div>

    </div>

  )
}