/**
 * @rag/ui - Shared UI Component Library
 * Platform-agnostic components based on shadcn/ui
 */

// Core Components
export { Button, buttonVariants } from './button'
export { Input } from './input'
export { Label } from './label'
export { Textarea } from './textarea'

// Layout Components
export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent } from './card'
export { Separator } from './separator'

// Form Components
export { Checkbox } from './checkbox'
export { Switch } from './switch'
export { Select, SelectGroup, SelectValue, SelectTrigger, SelectContent, SelectLabel, SelectItem, SelectSeparator, SelectScrollUpButton, SelectScrollDownButton } from './select'

// Data Display
export { Table, TableHeader, TableBody, TableFooter, TableHead, TableRow, TableCell, TableCaption } from './table'
export { Badge, badgeVariants } from './badge'
export { Avatar, AvatarImage, AvatarFallback } from './avatar'
export { Skeleton } from './skeleton'
export { Progress } from './progress'

// Custom Components
export { StatusBadge } from './status-badge'

// Feedback Components
export {
  AlertDialog,
  AlertDialogPortal,
  AlertDialogOverlay,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogFooter,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogAction,
  AlertDialogCancel,
} from './alert-dialog'

// Navigation
export { Tabs, TabsList, TabsTrigger, TabsContent } from './tabs'
