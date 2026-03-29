export default function CompetitorCallout() {
  return (
    <section className="py-24 md:py-32 border-t border-[#1a1a1a]">
      <div className="max-w-4xl mx-auto px-6 md:px-12 text-center">
        <p className="text-neutral-500 text-xs uppercase tracking-[0.25em] font-mono mb-12">
          Context
        </p>
        <p className="text-2xl md:text-3xl font-light text-neutral-300 leading-relaxed mb-6">
          Humane raised{' '}
          <span className="text-[#f0f0f0] font-medium">$230M</span>.
          Rabbit raised{' '}
          <span className="text-[#f0f0f0] font-medium">$180M</span>.
        </p>
        <p className="text-2xl md:text-3xl font-light text-neutral-300 leading-relaxed">
          We built what they were trying to build.
          <br />
          In 24 hours. For{' '}
          <span className="text-gold font-medium">£30</span>.
        </p>
      </div>
    </section>
  )
}
