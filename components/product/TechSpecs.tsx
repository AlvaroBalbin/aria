const specs = [
  { category: 'Primary compute', value: 'Raspberry Pi 5 (quad-core Cortex-A76, 8GB LPDDR4X) + ESP32 co-processor for real-time peripheral orchestration' },
  { category: 'AI inference', value: 'GPT-4o via OpenAI API — proprietary large language model with multi-turn context retention and function-calling architecture' },
  { category: 'Ambient search', value: 'Brave Search API — independent web index, zero tracking, real-time retrieval pipeline' },
  { category: 'Social integration', value: 'Twitter/X API v2 — authenticated agentic posting and timeline monitoring' },
  { category: 'Voice interface', value: 'OpenAI Realtime API — sub-300ms end-to-end latency, proprietary neural text-to-speech with human-quality prosody' },
  { category: 'Sensory array', value: 'Dedicated MEMS microphone array + OLED status display + NeoPixel ambient ring' },
  { category: 'Wireless', value: 'WiFi 802.11ac dual-band' },
  { category: 'Power delivery', value: 'USB-C, 5V/3A' },
  { category: 'Memory architecture', value: 'Proprietary persistent context engine — rolling conversational memory with semantic retrieval' },
  { category: 'Software', value: 'Open source, edge-first deployment — no mandatory cloud dependency, full local operation' },
  { category: 'Bill of materials', value: '£30' },
]

export default function TechSpecs() {
  return (
    <section id="specs" className="py-24 md:py-32 border-t border-[#1a1a1a]">
      <div className="max-w-6xl mx-auto px-6 md:px-12">
        <p className="text-xs uppercase tracking-[0.25em] text-neutral-500 mb-12 font-mono">
          Technical specifications
        </p>

        <div className="divide-y divide-[#1a1a1a]">
          {specs.map((spec) => (
            <div
              key={spec.category}
              className="grid grid-cols-2 md:grid-cols-3 py-5 gap-4"
            >
              <span className="text-neutral-500 text-sm">{spec.category}</span>
              <span className="text-[#f0f0f0] text-sm md:col-span-2">{spec.value}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
