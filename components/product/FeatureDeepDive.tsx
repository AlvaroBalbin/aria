interface FeatureDeepDiveProps {
  number: string
  title: string
  body: string
  imagePosition: 'left' | 'right'
  imageSrc?: string
}

export default function FeatureDeepDive({
  number,
  title,
  body,
  imagePosition,
  imageSrc,
}: FeatureDeepDiveProps) {
  const image = imageSrc ? (
    <img
      src={imageSrc}
      alt={title}
      className="w-full aspect-square object-cover border border-[#1a1a1a]"
    />
  ) : (
    <div className="w-full aspect-square bg-[#111111] border border-[#1a1a1a] flex items-center justify-center flex-shrink-0">
      <span className="text-neutral-700 text-xs font-mono tracking-widest uppercase">
        Product image
      </span>
    </div>
  )

  const copy = (
    <div className="flex flex-col justify-center">
      <p className="text-gold text-xs font-mono tracking-widest mb-6">{number}</p>
      <h2 className="text-3xl md:text-4xl font-light text-[#f0f0f0] mb-6 leading-tight">
        {title}
      </h2>
      <p className="text-neutral-400 text-base leading-relaxed max-w-md">{body}</p>
    </div>
  )

  return (
    <section className="py-24 md:py-32 border-t border-[#1a1a1a]">
      <div className="max-w-6xl mx-auto px-6 md:px-12">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 md:gap-20 items-center">
          {imagePosition === 'left' ? (
            <>
              {image}
              {copy}
            </>
          ) : (
            <>
              {copy}
              {image}
            </>
          )}
        </div>
      </div>
    </section>
  )
}
