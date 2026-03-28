import TeamCard from './TeamCard'

const team = [
  { name: 'Thomas Pickles', role: 'Hardware', initials: 'TP' },
  { name: 'Alvaro Balbin', role: 'Hardware', initials: 'AB' },
  { name: 'Ashwin Chandar', role: 'Software', initials: 'AC' },
  { name: 'Abdul Mahdi', role: 'Software', initials: 'AM' },
]

export default function Team() {
  return (
    <section className="py-24 md:py-32 border-t border-[#1a1a1a]">
      <div className="max-w-6xl mx-auto px-6 md:px-12">
        <p className="text-xs uppercase tracking-[0.25em] text-neutral-500 mb-4 font-mono">
          The team
        </p>
        <p className="text-neutral-400 text-sm mb-14">
          Four people. 24 hours. Bath Hackathon 2026.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          {team.map((member, i) => (
            <TeamCard
              key={i}
              name={member.name}
              role={member.role}
              initials={member.initials}
            />
          ))}
        </div>
      </div>
    </section>
  )
}
