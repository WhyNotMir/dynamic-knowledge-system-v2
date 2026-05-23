declare module 'lucide-react' {
  import * as React from 'react'

  export interface LucideProps extends React.SVGAttributes<SVGElement> {
    color?: string
    size?: number | string
    strokeWidth?: number | string
    absoluteStrokeWidth?: boolean
  }

  export type LucideIcon = React.ForwardRefExoticComponent<
    LucideProps & React.RefAttributes<SVGSVGElement>
  >

  export const LayoutDashboard: LucideIcon
  export const Upload: LucideIcon
  export const Inbox: LucideIcon
  export const BookOpen: LucideIcon
  export const MessageSquare: LucideIcon
  export const ChevronDown: LucideIcon
  export const ChevronRight: LucideIcon
  export const ChevronLeft: LucideIcon
  export const Plus: LucideIcon
  export const Check: LucideIcon
  export const CheckCircle: LucideIcon
  export const CheckCheck: LucideIcon
  export const X: LucideIcon
  export const Search: LucideIcon
  export const Trash2: LucideIcon
  export const Edit2: LucideIcon
  export const Eye: LucideIcon
  export const EyeOff: LucideIcon
  export const AlertTriangle: LucideIcon
  export const RefreshCw: LucideIcon
  export const FileText: LucideIcon
  export const FolderOpen: LucideIcon
  export const Send: LucideIcon
  export const ExternalLink: LucideIcon
  export const Copy: LucideIcon
  export const Clock: LucideIcon
  export const Hammer: LucideIcon
}
