const PRODUCT_API = process.env.NEXT_PUBLIC_PRODUCT_API_URL ?? "http://localhost:10126/api/products"
const CHAT_API = process.env.NEXT_PUBLIC_CHAT_API_URL ?? "http://localhost:10126/api/chat"

// ==========================
// PRODUCTS
// ==========================

export async function getProducts(category?: string, subcategory?: string) {
  const params = new URLSearchParams()
  if (category) params.append("category", category)
  if (subcategory) params.append("subcategory", subcategory)

  const url = params.toString() ? `${PRODUCT_API}?${params}` : PRODUCT_API
  const res = await fetch(url, { cache: "no-store" })
  if (!res.ok) throw new Error("Failed to fetch products")
  return res.json()
}

export async function getCategories(): Promise<Record<string, string[]>> {
  const res = await fetch(`${PRODUCT_API}/categories/all`, { cache: "no-store" })
  if (!res.ok) throw new Error("Failed to fetch categories")
  return res.json()
}

export async function getProduct(id: string) {
  const res = await fetch(`${PRODUCT_API}/${id}`, { cache: "no-store" })
  if (!res.ok) throw new Error("Product not found")
  return res.json()
}

// ==========================
// CHAT
// ==========================

export interface SendMessagePayload {
  message: string
  session_id?: string
  context_product_id?: string
}

export interface SendMessageResponse {
  success: boolean
  data?: {
    session?: { session_id: string; created_at: string }
    status?: string
    user_message?: {
      message_id: string
      content: string
      timestamp: string
    }
  }
}

export async function sendMessage(
  payload: SendMessagePayload
): Promise<SendMessageResponse> {
  const res = await fetch(`${CHAT_API}/assistant_chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error("Failed to send message")
  return res.json()
}

export function createSSE(sessionId: string): EventSource {
  return new EventSource(`${CHAT_API}/sse/${sessionId}`)
}