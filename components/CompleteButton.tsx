"use client";
import { useEffect, useState } from "react";
import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";

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
    <Button
      onClick={toggle}
      variant={done ? "default" : "outline"}
      size="sm"
    >
      <Check className="h-4 w-4" />
      {done ? "Completed" : "Mark complete"}
    </Button>
  );
}
