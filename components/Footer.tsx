export default function Footer() {
  return (
    <footer className="border-t border-[#1a1a1a] py-8">
      <div className="max-w-6xl mx-auto px-6 md:px-12 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <span className="text-gold text-xs font-mono tracking-[0.25em] uppercase">
          ARIA
        </span>
        <span className="text-neutral-600 text-xs">
          Built at Bath Hackathon 2026
        </span>
      </div>
    </footer>
  )
}
