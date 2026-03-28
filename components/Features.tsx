import FeatureCard from './FeatureCard'

const features = [
  {
    number: '01',
    title: 'Ambient memory',
    body: 'Always listening, building context before you even ask. ARIA knows what you worked on, who you spoke to, and what was decided, without you lifting a finger.',
  },
  {
    number: '02',
    title: 'Agentic AI',
    body: 'Searches the web, saves facts, retrieves context, sets reminders. ARIA does not just answer questions. It takes real actions on your behalf.',
  },
  {
    number: '03',
    title: 'Voice identity',
    body: 'Responds in your own cloned voice. Not a robot. Not a generic assistant. You, distilled. Open-source TTS you control entirely.',
  },
  {
    number: '04',
    title: 'Yours entirely',
    body: 'Open source, local-first, £30 in hardware. Your data stays on your own device. No subscription. No cloud lock-in. No corporation between you and your memories.',
  },
]

export default function Features() {
  return (
    <section className="py-24 md:py-32 border-t border-[#1a1a1a]">
      <div className="max-w-6xl mx-auto px-6 md:px-12">
        <p className="text-xs uppercase tracking-[0.25em] text-neutral-500 mb-12 font-mono">
          Why ARIA
        </p>

        <div className="border-l-2 border-gold pl-6 mb-20 max-w-3xl">
          <p className="text-neutral-300 text-xl md:text-2xl font-light leading-relaxed">
            Humane raised{' '}
            <span className="text-[#f0f0f0] font-medium">$230M</span>.
            Rabbit raised{' '}
            <span className="text-[#f0f0f0] font-medium">$180M</span>.
            We built what they were trying to build, in 24 hours, for{' '}
            <span className="text-gold font-medium">£30</span>.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-[#1a1a1a]">
          {features.map((feature) => (
            <FeatureCard
              key={feature.number}
              number={feature.number}
              title={feature.title}
              body={feature.body}
            />
          ))}
        </div>
      </div>
    </section>
  )
}
