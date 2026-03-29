export default function Nav() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 md:px-12 py-5 bg-[#080808]/80 backdrop-blur-sm border-b border-[#1a1a1a]">
      <span className="text-gold text-xs font-mono tracking-[0.25em] uppercase">
        ARIA
      </span>
      <a
        href="/product"
        className="border border-[#2a2a2a] text-neutral-300 px-5 py-2 text-xs font-medium hover:border-neutral-500 transition-colors"
      >
        View product
      </a>
    </nav>
  )
}
