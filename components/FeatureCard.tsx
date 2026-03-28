interface FeatureCardProps {
  number: string
  title: string
  body: string
}

export default function FeatureCard({ number, title, body }: FeatureCardProps) {
  return (
    <div className="bg-[#111111] p-8 md:p-10">
      <p className="text-gold text-xs font-mono tracking-widest mb-6">
        {number}
      </p>
      <h3 className="text-lg font-medium text-[#f0f0f0] mb-3">{title}</h3>
      <p className="text-neutral-400 text-base leading-relaxed">{body}</p>
    </div>
  )
}
