export default function ProductCTABand() {
  return (
    <section className="py-24 md:py-32 border-t border-[#1a1a1a] text-center">
      <div className="max-w-2xl mx-auto px-6 md:px-12">
        <p className="text-xs uppercase tracking-[0.25em] text-neutral-500 mb-6 font-mono">
          Get ARIA
        </p>
        <h2 className="text-3xl md:text-4xl font-light text-[#f0f0f0] mb-10">
          Ready to get ARIA?
        </h2>
        <a
          href="https://aria-wheat.vercel.app"
          className="inline-block bg-gold text-[#080808] px-10 py-4 text-sm font-medium hover:opacity-90 transition-opacity"
        >
          Join the waitlist
        </a>
      </div>
    </section>
  )
}
