import Navbar from "@/components/navbar/Navbar"
import Footer from "@/components/footer/Footer"
import AssistantWidget from "@/components/assistant/assistantWidget"
import "./globals.css"

export default function RootLayout({ children }: any) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        {children}
        <Footer />
        <AssistantWidget />
      </body>
    </html>
  )
}