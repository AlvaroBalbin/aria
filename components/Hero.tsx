import WaitlistForm from './WaitlistForm'

export default function Hero() {
  return (
    <section className="min-h-screen flex flex-col justify-center py-24">
      <div className="max-w-6xl mx-auto px-6 md:px-12">
        <p className="text-xs uppercase tracking-[0.25em] text-gold mb-8 font-mono">
          ARIA
        </p>

        <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-light tracking-tight leading-none text-[#f0f0f0] max-w-4xl">
          The AI you wear.
        </h1>

        <p className="text-lg md:text-xl text-neutral-400 font-light mt-6 max-w-xl leading-relaxed">
          It knows you. It remembers everything. It takes real actions.
        </p>

        <div className="mt-12 border-l-2 border-gold pl-6 max-w-xl">
          <p className="text-neutral-300 text-base md:text-lg font-light leading-relaxed italic">
            Every AI assistant forgets you the moment you close the app.
            ARIA does not.
          </p>
        </div>

        <WaitlistForm />
      </div>
    </section>
  )
}
