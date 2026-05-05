export default function Footer() {
  return (
    <footer className="bg-gray-100 mt-20 border-t">
      <div className="max-w-6xl mx-auto px-6 py-12 grid grid-cols-4 gap-8 text-sm">

        <div>
          <h3 className="font-semibold mb-3">Store</h3>
          <ul className="space-y-2 text-gray-600">
            <li>All Products</li>
            <li>New Arrivals</li>
            <li>Best Sellers</li>
          </ul>
        </div>

        <div>
          <h3 className="font-semibold mb-3">Support</h3>
          <ul className="space-y-2 text-gray-600">
            <li>Contact Us</li>
            <li>Warranty</li>
            <li>FAQ</li>
          </ul>
        </div>

        <div>
          <h3 className="font-semibold mb-3">Company</h3>
          <ul className="space-y-2 text-gray-600">
            <li>About</li>
          </ul>
        </div>

        <div>
          <h3 className="font-semibold mb-3">Follow</h3>
          <ul className="space-y-2 text-gray-600">
            <li>Twitter</li>
            <li>LinkedIn</li>
            <li>GitHub</li>
          </ul>
        </div>

      </div>

      <div className="text-center text-xs text-gray-500 pb-6">
        © 2026 TechStore. All rights reserved.
      </div>
    </footer>
  )
}