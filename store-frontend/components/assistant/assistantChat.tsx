"use client"

import { useState, useRef, useEffect } from "react"
import { X, Send } from "lucide-react"
import { sendMessage, createSSE } from "@/lib/api"

type Message = {
  role: "user" | "assistant"
  content: string
  streaming?: boolean
}

export default function AssistantChat({
  onClose,
  contextProductId,
}: {
  onClose: () => void
  contextProductId?: string
}) {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Xin chào! Mình có thể giúp gì cho bạn? 👋" },
  ])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const sessionIdRef = useRef<string | null>(null)
  const sseRef = useRef<EventSource | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  useEffect(() => {
    return () => sseRef.current?.close()
  }, [])

  // ── State helpers ─────────────────────────────────────────

  const appendToken = (token: string) => {
    setMessages(prev => {
      const updated = [...prev]
      const last = updated[updated.length - 1]
      if (last?.role === "assistant") {
        updated[updated.length - 1] = {
          ...last,
          content: last.content + token,
          streaming: true,
        }
      }
      return updated
    })
  }

  const finalizeStream = () => {
    setMessages(prev => {
      const updated = [...prev]
      const last = updated[updated.length - 1]
      if (last?.role === "assistant") {
        updated[updated.length - 1] = { ...last, streaming: false }
      }
      return updated
    })
    setLoading(false)
    inputRef.current?.focus()
  }

  const showError = (msg = "Có lỗi xảy ra, thử lại nhé!") => {
    setMessages(prev => {
      const updated = [...prev]
      const last = updated[updated.length - 1]
      if (last?.role === "assistant" && last.content === "") {
        updated[updated.length - 1] = { role: "assistant", content: msg, streaming: false }
      } else {
        updated.push({ role: "assistant", content: msg, streaming: false })
      }
      return updated
    })
    setLoading(false)
  }

  // ── SSE — mở 1 lần, giữ mãi ──────────────────────────────

  const openSSE = (sessionId: string) => {
    if (sseRef.current) return

    const evtSource = createSSE(sessionId)
    sseRef.current = evtSource

    evtSource.onmessage = (e) => {
      if (e.data === "[DONE]") {
        finalizeStream()
        return
      }
      if (e.data.startsWith("[ERROR]")) {
        showError()
        return
      }
      appendToken(e.data)
    }

    evtSource.onerror = () => {
      if (loading) showError("Mất kết nối, thử lại nhé!")
    }
  }

  // ── Send ──────────────────────────────────────────────────

  const send = async () => {
    if (!input.trim() || loading) return

    const content = input.trim()
    setInput("")
    setLoading(true)

    setMessages(prev => [
      ...prev,
      { role: "user", content },
      { role: "assistant", content: "", streaming: true },
    ])

    try {
      const data = await sendMessage({
        message: content,
        ...(sessionIdRef.current && { session_id: sessionIdRef.current }),
        ...(contextProductId && { context_product_id: contextProductId }),
      })

      if (!data.success) throw new Error("Request failed")

      const sessionId = data?.data?.session?.session_id ?? sessionIdRef.current
      if (!sessionId) throw new Error("Missing session_id")

      sessionIdRef.current = sessionId
      openSSE(sessionId)

    } catch {
      showError()
    }
  }

  // ── Render ────────────────────────────────────────────────

  return (
    <div className="w-80 h-[460px] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-gray-200">

      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-blue-600">
        <div className="flex items-center gap-2">
          <img src="/assistant-icon.png" className="w-8 h-8 object-contain bg-white rounded-full p-1" />
          <div>
            <p className="text-white font-semibold text-sm">Trợ lý TechStore</p>
            <p className="text-blue-200 text-xs">Luôn sẵn sàng hỗ trợ</p>
          </div>
        </div>
        <button onClick={onClose}>
          <X size={18} className="text-white hover:text-blue-200" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-1 bg-gray-100">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex items-end gap-1.5 ${m.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {m.role === "assistant" && (
              <img src="/assistant-icon.png" className="w-5 h-5 object-contain rounded-full bg-white border shrink-0 mb-0.5" />
            )}
            <div className={`max-w-[72%] px-3 py-1.5 rounded-2xl text-sm leading-snug ${
              m.role === "user"
                ? "bg-blue-600 text-white rounded-br-none"
                : "bg-white text-gray-800 rounded-bl-none shadow-sm"
            }`}>
              {m.role === "assistant" && m.content === "" && m.streaming ? (
                <div className="flex gap-1 items-center py-0.5">
                  <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:0ms]" />
                  <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:150ms]" />
                  <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:300ms]" />
                </div>
              ) : (
                <>
                  {m.content}
                  {m.streaming && (
                    <span className="inline-block w-0.5 h-3.5 bg-gray-500 ml-0.5 align-middle animate-pulse" />
                  )}
                </>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex items-center gap-2 px-3 py-3 border-t border-gray-200 bg-white">
        <input
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && send()}
          placeholder="Aa"
          disabled={loading}
          className="flex-1 bg-gray-200 text-gray-900 text-sm rounded-full px-4 py-2 outline-none placeholder:text-gray-500 disabled:opacity-60"
        />
        <button
          onClick={send}
          disabled={!input.trim() || loading}
          className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center hover:bg-blue-700 disabled:opacity-40 transition"
        >
          <Send size={14} className="text-white" />
        </button>
      </div>
    </div>
  )
}