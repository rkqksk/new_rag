# UI Component Examples

This document provides usage examples for the 8 newly added UI components following the Pure Black design system.

## 1. Dialog Component

Modal dialogs for important user interactions.

```tsx
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"

export function DialogExample() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Open Dialog</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Confirm Action</DialogTitle>
          <DialogDescription>
            Are you sure you want to proceed with this action?
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <Button>Confirm</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
```

## 2. Popover Component

Floating popovers for contextual information.

```tsx
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Button } from "@/components/ui/button"

export function PopoverExample() {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline">Open Popover</Button>
      </PopoverTrigger>
      <PopoverContent>
        <div className="space-y-2">
          <h4 className="font-medium">Settings</h4>
          <p className="text-sm text-stone-400">
            Configure your preferences here.
          </p>
        </div>
      </PopoverContent>
    </Popover>
  )
}
```

## 3. Tooltip Component

Hover tooltips for additional context.

```tsx
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { Button } from "@/components/ui/button"

export function TooltipExample() {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="outline">Hover me</Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>Additional information</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
```

## 4. Accordion Component

Collapsible sections for organizing content.

```tsx
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"

export function AccordionExample() {
  return (
    <Accordion type="single" collapsible className="w-full">
      <AccordionItem value="item-1">
        <AccordionTrigger>What is RAG?</AccordionTrigger>
        <AccordionContent>
          Retrieval-Augmented Generation combines information retrieval with text generation.
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-2">
        <AccordionTrigger>How does it work?</AccordionTrigger>
        <AccordionContent>
          It retrieves relevant documents and uses them to generate contextual responses.
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  )
}
```

## 5. Dropdown Menu Component

Context menus with multiple options.

```tsx
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuCheckboxItem,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"

export function DropdownMenuExample() {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline">Options</Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        <DropdownMenuLabel>Actions</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem>Edit</DropdownMenuItem>
        <DropdownMenuItem>Duplicate</DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem className="text-red-400">Delete</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

export function DropdownMenuCheckboxExample() {
  const [showPanel, setShowPanel] = React.useState(true)
  const [showToolbar, setShowToolbar] = React.useState(false)

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline">View</Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        <DropdownMenuLabel>Toggle Panels</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuCheckboxItem
          checked={showPanel}
          onCheckedChange={setShowPanel}
        >
          Side Panel
        </DropdownMenuCheckboxItem>
        <DropdownMenuCheckboxItem
          checked={showToolbar}
          onCheckedChange={setShowToolbar}
        >
          Toolbar
        </DropdownMenuCheckboxItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
```

## 6. Toast Component

Notification toasts for user feedback.

```tsx
import {
  Toast,
  ToastAction,
  ToastClose,
  ToastDescription,
  ToastProvider,
  ToastTitle,
  ToastViewport,
} from "@/components/ui/toast"
import { Button } from "@/components/ui/button"

// In your app layout or root component
export function ToastProviderExample() {
  return (
    <ToastProvider>
      {/* Your app content */}
      <ToastViewport />
    </ToastProvider>
  )
}

// Usage with a custom hook (create hooks/use-toast.ts)
export function ToastExample() {
  const { toast } = useToast()

  return (
    <Button
      onClick={() => {
        toast({
          title: "Success",
          description: "Your changes have been saved.",
        })
      }}
    >
      Show Toast
    </Button>
  )
}

// Direct usage
export function ToastDirectExample() {
  const [open, setOpen] = React.useState(false)

  return (
    <>
      <Button onClick={() => setOpen(true)}>Show Toast</Button>
      <Toast open={open} onOpenChange={setOpen}>
        <ToastTitle>Notification</ToastTitle>
        <ToastDescription>This is a notification message.</ToastDescription>
        <ToastClose />
      </Toast>
    </>
  )
}
```

## 7. Alert Component

Static alerts for important messages.

```tsx
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

export function AlertExample() {
  return (
    <Alert>
      <AlertTitle>Information</AlertTitle>
      <AlertDescription>
        This is an informational alert message.
      </AlertDescription>
    </Alert>
  )
}

export function AlertDestructiveExample() {
  return (
    <Alert variant="destructive">
      <AlertTitle>Error</AlertTitle>
      <AlertDescription>
        An error occurred while processing your request.
      </AlertDescription>
    </Alert>
  )
}
```

## 8. Radio Component

Radio button groups for single selection.

```tsx
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio"
import { Label } from "@/components/ui/label"

export function RadioExample() {
  return (
    <RadioGroup defaultValue="option-1">
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="option-1" id="option-1" />
        <Label htmlFor="option-1">Option 1</Label>
      </div>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="option-2" id="option-2" />
        <Label htmlFor="option-2">Option 2</Label>
      </div>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="option-3" id="option-3" />
        <Label htmlFor="option-3">Option 3</Label>
      </div>
    </RadioGroup>
  )
}

export function RadioWithStateExample() {
  const [value, setValue] = React.useState("comfortable")

  return (
    <RadioGroup value={value} onValueChange={setValue}>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="compact" id="compact" />
        <Label htmlFor="compact">Compact</Label>
      </div>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="comfortable" id="comfortable" />
        <Label htmlFor="comfortable">Comfortable</Label>
      </div>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="spacious" id="spacious" />
        <Label htmlFor="spacious">Spacious</Label>
      </div>
    </RadioGroup>
  )
}
```

## Design System Compliance

All components follow the Pure Black design system:

1. **Pure Black Background**: `bg-black` (#000000)
2. **NO Icons**: Unicode characters (✕, ▼, ▲, ▶, ✓, ●) instead of icon libraries
3. **Natural Theme**: Minimal, organic styling with stone colors
4. **Consistent Border**: `border-stone-800` for all borders
5. **Text Colors**:
   - Primary: `text-stone-100`
   - Secondary: `text-stone-400`
   - Destructive: `text-red-100` on `bg-red-950`

## Installation

Dependencies are already added to `package.json`. Install with:

```bash
cd apps/web
pnpm install
```

## Available Components (25 Total)

**Original (17)**:
- alert-dialog.tsx
- avatar.tsx
- badge.tsx
- button.tsx
- card.tsx
- checkbox.tsx
- input.tsx
- label.tsx
- progress.tsx
- select.tsx
- separator.tsx
- skeleton.tsx
- status-badge.tsx
- switch.tsx
- table.tsx
- tabs.tsx
- textarea.tsx

**New (8)**:
- dialog.tsx ✨
- popover.tsx ✨
- tooltip.tsx ✨
- accordion.tsx ✨
- dropdown-menu.tsx ✨
- toast.tsx ✨
- alert.tsx ✨
- radio.tsx ✨
