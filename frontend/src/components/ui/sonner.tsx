"use client"

import { Toaster as Sonner, ToasterProps } from "sonner"
import { useUIStore } from "@/stores"

const Toaster = ({ ...props }: ToasterProps) => {
  const theme = useUIStore((state) => state.theme)

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      className="toaster group"
      style={
        {
          "--normal-bg": "var(--popover)",
          "--normal-text": "var(--popover-foreground)",
          "--normal-border": "var(--border)",
        } as React.CSSProperties
      }
      {...props}
    />
  )
}

export { Toaster }
