import { cn } from '@/lib/utils'

interface CroScoreGaugeProps {
  score: number
  size?: 'sm' | 'md' | 'lg'
  showBand?: boolean
}

function getScoreColor(score: number): string {
  if (score >= 80) return 'hsl(var(--score-optimized))'
  if (score >= 60) return '#F59E0B'
  if (score >= 40) return 'hsl(var(--accent))'
  return 'hsl(var(--score-critical))'
}

function getScoreBand(score: number): string {
  if (score >= 80) return 'Optimized'
  if (score >= 60) return 'Needs Work'
  if (score >= 40) return 'High Risk'
  return 'Critical'
}

const sizes = {
  sm: { outer: 80, stroke: 6, fontSize: 'text-lg', labelSize: 'text-[9px]' },
  md: { outer: 120, stroke: 8, fontSize: 'text-3xl', labelSize: 'text-xs' },
  lg: { outer: 160, stroke: 10, fontSize: 'text-5xl', labelSize: 'text-sm' },
}

export default function CroScoreGauge({ score, size = 'md', showBand = true }: CroScoreGaugeProps) {
  const { outer, stroke, fontSize, labelSize } = sizes[size]
  const radius = (outer - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const progress = Math.max(0, Math.min(100, score))
  const offset = circumference - (progress / 100) * circumference
  const color = getScoreColor(score)

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={outer} height={outer} className="-rotate-90">
        {/* Background circle */}
        <circle
          cx={outer / 2}
          cy={outer / 2}
          r={radius}
          fill="none"
          stroke="hsl(var(--border))"
          strokeWidth={stroke}
        />
        {/* Progress circle */}
        <circle
          cx={outer / 2}
          cy={outer / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div
        className="absolute flex flex-col items-center justify-center"
        style={{ width: outer, height: outer }}
      >
        <span className={cn('font-heading font-bold', fontSize)} style={{ color }}>
          {score}
        </span>
      </div>
      {showBand && (
        <span className={cn('font-medium', labelSize)} style={{ color }}>
          {getScoreBand(score)}
        </span>
      )}
    </div>
  )
}

export { getScoreColor, getScoreBand }
