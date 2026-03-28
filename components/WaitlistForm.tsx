'use client'

import { useState, FormEvent } from 'react'

const INITIAL_COUNT = 1247

export default function WaitlistForm() {
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [count, setCount] = useState(INITIAL_COUNT)
  const [error, setError] = useState('')

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Please enter a valid email address.')
      return
    }
    setError('')
    setSubmitted(true)
    setCount((prev) => prev + 1)
  }

  return (
    <div className="mt-10">
      <p className="text-sm text-neutral-500 mb-5 font-mono tracking-wide">
        {count.toLocaleString()} people on the waitlist
      </p>

      {submitted ? (
        <p
          role="status"
          className="text-neutral-300 text-base leading-relaxed max-w-md border-l-2 border-gold pl-5"
        >
          You're on the waitlist. You will receive updates and communications
          from the ARIA team.
        </p>
      ) : (
        <form onSubmit={handleSubmit} noValidate>
          <div className="flex flex-col sm:flex-row gap-3 max-w-md">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              aria-label="Email address"
              className="flex-1 bg-[#111111] border border-[#1a1a1a] text-[#f0f0f0] placeholder-neutral-600 px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-gold"
            />
            <button
              type="submit"
              className="bg-gold text-[#080808] px-6 py-3 text-sm font-medium hover:opacity-90 transition-opacity whitespace-nowrap"
            >
              Join waitlist
            </button>
          </div>
          {error && (
            <p className="text-red-400 text-xs mt-2" role="alert">
              {error}
            </p>
          )}
        </form>
      )}
    </div>
  )
}
