import ProductHero from '@/components/product/ProductHero'
import FeatureDeepDive from '@/components/product/FeatureDeepDive'
import CompetitorCallout from '@/components/product/CompetitorCallout'
import TechSpecs from '@/components/product/TechSpecs'
import StatsRow from '@/components/product/StatsRow'
import ProductCTABand from '@/components/product/ProductCTABand'
import Footer from '@/components/Footer'

export const metadata = {
  title: 'ARIA - Product',
  description: 'The AI that lives on your desk. Knows your life. Takes real actions.',
}

export default function ProductPage() {
  return (
    <main>
      <ProductHero />

      <section className="py-24 md:py-32 border-t border-[#1a1a1a]">
        <div className="max-w-4xl mx-auto px-6 md:px-12 text-center">
          <p className="text-3xl md:text-4xl lg:text-5xl font-light text-[#f0f0f0] leading-tight">
            Every AI assistant forgets you the moment you close the app.
            <br />
            <span className="text-neutral-400">ARIA does not.</span>
          </p>
        </div>
      </section>

      <FeatureDeepDive
        number="01"
        title="Ambient memory"
        body="Always listening, always building context. ARIA knows what you worked on, who you spoke to, and what you decided, before you even ask."
        imagePosition="right"
      />
      <FeatureDeepDive
        number="02"
        title="Agentic AI"
        body="Searches the web with Brave Search, saves facts, sets reminders, retrieves context, and posts to social media. ARIA does not just answer. It acts."
        imagePosition="left"
      />
      <FeatureDeepDive
        number="03"
        title="Voice identity"
        body="Powered by OpenAI Realtime API, ARIA speaks with ultra-low latency in a voice that sounds genuinely human. No delays. No robotic tone. A real conversation."
        imagePosition="right"
      />

      <CompetitorCallout />
      <TechSpecs />
      <StatsRow />
      <ProductCTABand />
      <Footer />
    </main>
  )
}
