export default function ProductHero() {
  return (
    <section className="min-h-screen flex flex-col justify-center text-center py-24">
      <div className="max-w-5xl mx-auto px-6 md:px-12">
        <img
          src="/aria_logo.png"
          alt="ARIA"
          className="w-24 h-24 mx-auto mb-8 object-contain"
        />

        <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-light tracking-tight leading-none text-[#f0f0f0]">
          The AI that lives
          <br />
          on your desk.
        </h1>

        <p className="text-lg md:text-xl text-neutral-400 font-light mt-8 max-w-xl mx-auto leading-relaxed">
          Knows your life. Remembers everything. Takes real actions.
        </p>

        <div className="mt-12 flex flex-col sm:flex-row gap-4 justify-center">
          <a
            href="https://aria-wheat.vercel.app"
            className="bg-gold text-[#080808] px-8 py-3 text-sm font-medium hover:opacity-90 transition-opacity"
          >
            Join the waitlist
          </a>
          <a
            href="#specs"
            className="border border-[#2a2a2a] text-neutral-300 px-8 py-3 text-sm font-medium hover:border-neutral-500 transition-colors"
          >
            View specs
          </a>
        </div>
      </div>
    </section>
  )
}
