interface TeamCardProps {
  name: string
  role: string
  initials: string
}

export default function TeamCard({ name, role, initials }: TeamCardProps) {
  return (
    <div className="bg-[#111111] border border-[#1a1a1a] p-6">
      <div className="w-14 h-14 rounded-full bg-[#080808] border border-[#2a2a2a] flex items-center justify-center">
        <span className="text-gold text-xs font-mono tracking-widest">
          {initials}
        </span>
      </div>
      <p className="text-[#f0f0f0] text-sm font-medium mt-5">{name}</p>
      <p className="text-neutral-500 text-sm mt-1">{role}</p>
    </div>
  )
}
