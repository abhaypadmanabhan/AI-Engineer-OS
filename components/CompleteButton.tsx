"use client";
import { useEffect, useState } from "react";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export function CompleteButton({ slug }: { slug: string[] }) {
  const key = `done:${slug.join("/")}`;
  const [done, setDone] = useState(false);

  useEffect(() => {
    setDone(localStorage.getItem(key) === "1");
  }, [key]);

  function toggle() {
    const next = !done;
    setDone(next);
    if (next) localStorage.setItem(key, "1");
    else localStorage.removeItem(key);
    window.dispatchEvent(new Event("storage"));
  }

  return (
    <button
      onClick={toggle}
      className={cn(
        "inline-flex items-center gap-2 rounded border px-3 py-1.5 text-sm font-medium transition-colors",
        done
          ? "border-accent bg-accent/10 text-accent"
          : "border-border hover:border-accent"
      )}
    >
      <Check className="h-4 w-4" />
      {done ? "Completed" : "Mark complete"}
    </button>
  );
}
