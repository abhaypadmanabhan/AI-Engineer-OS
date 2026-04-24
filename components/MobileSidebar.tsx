"use client";
import { useState } from "react";
import { Menu } from "lucide-react";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Sidebar } from "@/components/Sidebar";

type Lesson = { slug: string[]; title: string; minutes: number; order: number };
type Group = { layerSlug: string; layer: number; title: string; lessons: Lesson[] };

export function MobileSidebar({ groups }: { groups: Group[] }) {
  const [open, setOpen] = useState(false);
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="md:hidden" aria-label="Open curriculum">
          <Menu className="h-5 w-5" />
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-80 p-0">
        <SheetTitle className="sr-only">Curriculum</SheetTitle>
        <div onClick={() => setOpen(false)}>
          <Sidebar groups={groups} />
        </div>
      </SheetContent>
    </Sheet>
  );
}
