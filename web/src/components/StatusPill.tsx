import type { StopStatus } from '../api/types'

const LABELS: Record<StopStatus, string> = {
  pending: 'Pending',
  planned: 'Planned',
  in_transit: 'In transit',
  delivered: 'Delivered',
  failed: 'Failed',
  cancelled: 'Cancelled',
}

export function StatusPill({ status }: { status: StopStatus }) {
  return <span className={`pill pill--${status}`}>{LABELS[status]}</span>
}
