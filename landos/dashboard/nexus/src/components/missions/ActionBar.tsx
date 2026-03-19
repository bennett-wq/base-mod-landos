import { Upload, Search, Bot, FileText } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface ActionCardProps {
  icon: LucideIcon
  title: string
  description: string
}

function ActionCard({ icon: Icon, title, description }: ActionCardProps) {
  return (
    <div className="group cursor-pointer rounded-xl bg-surface-container-low p-5 transition-all hover:bg-white">
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-surface-container transition-all group-hover:copper-gradient">
        <Icon
          size={18}
          strokeWidth={2}
          className="text-primary transition-colors group-hover:text-white"
        />
      </div>
      <h3 className="mb-1 text-sm font-bold text-on-surface">{title}</h3>
      <p className="text-xs leading-relaxed text-on-surface-variant">{description}</p>
    </div>
  )
}

const actions: ActionCardProps[] = [
  {
    icon: Upload,
    title: 'Upload Data',
    description: 'Import parcel or listing datasets',
  },
  {
    icon: Search,
    title: 'Polygon Search',
    description: 'Draw custom search boundaries',
  },
  {
    icon: Bot,
    title: 'Deploy Agent',
    description: 'Launch targeted intelligence agent',
  },
  {
    icon: FileText,
    title: 'Generate Report',
    description: 'Export analysis for stakeholders',
  },
]

export function ActionBar() {
  return (
    <section className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {actions.map((action) => (
        <ActionCard key={action.title} {...action} />
      ))}
    </section>
  )
}
