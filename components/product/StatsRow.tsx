const stats = [
  { value: '£30', label: 'in hardware' },
  { value: '0', label: 'subscriptions' },
  { value: '100%', label: 'local' },
]

export default function StatsRow() {
  return (
    <section className="py-24 md:py-32 border-t border-[#1a1a1a]">
      <div className="max-w-6xl mx-auto px-6 md:px-12">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-px bg-[#1a1a1a] mb-16">
          {stats.map((stat) => (
            <div key={stat.label} className="bg-[#080808] p-10 text-center">
              <p className="text-5xl md:text-6xl font-light text-gold mb-3">
                {stat.value}
              </p>
              <p className="text-neutral-500 text-sm uppercase tracking-widest font-mono">
                {stat.label}
              </p>
            </div>
          ))}
        </div>

        <p className="text-center text-neutral-400 text-base leading-relaxed max-w-xl mx-auto">
          Your data never leaves your home. No corporation between you and your memories.
        </p>
      </div>
    </section>
  )
}
