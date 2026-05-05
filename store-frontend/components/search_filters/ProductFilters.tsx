"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getCategories } from "@/lib/api";

export function Filters() {
  const router = useRouter();

  const [categories, setCategories] = useState<Record<string, string[]>>({});
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [activeSub, setActiveSub] = useState<string | null>(null);

  useEffect(() => {
    getCategories().then(setCategories);
    const params = new URLSearchParams(window.location.search);
    setActiveCategory(params.get("category"));
    setActiveSub(params.get("subcategory"));
  }, []);

  const toggleCategory = (cat: string) => {
  const next = activeCategory === cat ? null : cat;
  setActiveCategory(next);
  setActiveSub(null);
  const query = new URLSearchParams();
  if (next) query.set("category", next);
  router.replace(`/?${query.toString()}`);
  router.refresh();
};

const toggleSub = (sub: string) => {
  const next = activeSub === sub ? null : sub;
  setActiveSub(next);
  const query = new URLSearchParams();
  if (activeCategory) query.set("category", activeCategory);
  if (next) query.set("subcategory", next);
  router.replace(`/?${query.toString()}`);
  router.refresh();
};

  const subs = activeCategory ? (categories[activeCategory] ?? []) : [];

  return (
    <div className="mb-8 space-y-3">

      <div className="flex flex-wrap gap-2">
        {Object.keys(categories).map((c) => (
          <button
            key={c}
            onClick={() => toggleCategory(c)}
            className={`px-4 py-2 rounded-full text-sm capitalize transition
              ${activeCategory === c ? "bg-violet-600 text-white" : "bg-zinc-700 text-gray-300"}`}
          >
            {c}
          </button>
        ))}
      </div>

      {subs.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {subs.map((s) => (
            <button
              key={s}
              onClick={() => toggleSub(s)}
              className={`px-3 py-1 rounded-full text-sm capitalize transition
                ${activeSub === s ? "bg-violet-600 text-white" : "bg-zinc-700 text-gray-300"}`}
            >
              {s}
            </button>
          ))}
        </div>
      )}

    </div>
  );
}