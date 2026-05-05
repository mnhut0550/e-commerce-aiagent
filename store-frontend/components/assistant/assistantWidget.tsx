"use client"

import { useState } from "react"
import AssistantChat from "./assistantChat"

export default function AssistantWidget() {
  const [open, setOpen] = useState(false)

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">
      {open ? (
        <AssistantChat onClose={() => setOpen(false)} />
      ) : (
        <button
          onClick={() => setOpen(true)}
          className="hover:scale-110 transition w-24 h-24 rounded-full overflow-hidden shadow-xl bg-blue-100"
        >
          <img
            src="/assistant-icon.png"
            className="w-full h-full object-contain mix-blend-multiply scale-75"
          />
        </button>
      )}
    </div>
  )
}