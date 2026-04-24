import fs from "node:fs";
import path from "node:path";
import matter from "gray-matter";
import { frontmatterSchema, type Frontmatter } from "./schema";

export const CONTENT_ROOT = path.join(process.cwd(), "content", "modules");

export type LessonMeta = {
  slug: string[];            // e.g. ["00-setup", "01-toolchain"]
  path: string;              // absolute fs path to index.mdx
  frontmatter: Frontmatter;
};

export type ModuleGroup = {
  layerSlug: string;         // "00-setup"
  layer: number;             // 0
  title: string;             // "Setup"
  lessons: LessonMeta[];
};

function titleCase(s: string) {
  return s
    .replace(/^\d+-/, "")
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export function getAllLessons(): LessonMeta[] {
  if (!fs.existsSync(CONTENT_ROOT)) return [];
  const layers = fs
    .readdirSync(CONTENT_ROOT)
    .filter((d) => fs.statSync(path.join(CONTENT_ROOT, d)).isDirectory())
    .sort();
  const lessons: LessonMeta[] = [];
  for (const layer of layers) {
    const layerDir = path.join(CONTENT_ROOT, layer);
    const lessonDirs = fs
      .readdirSync(layerDir)
      .filter((d) => fs.statSync(path.join(layerDir, d)).isDirectory())
      .sort();
    for (const lesson of lessonDirs) {
      const indexPath = path.join(layerDir, lesson, "index.mdx");
      if (!fs.existsSync(indexPath)) continue;
      const raw = fs.readFileSync(indexPath, "utf8");
      const { data } = matter(raw);
      const parsed = frontmatterSchema.safeParse(data);
      if (!parsed.success) {
        console.warn(`[content] bad frontmatter in ${indexPath}:`, parsed.error.issues);
        continue;
      }
      lessons.push({ slug: [layer, lesson], path: indexPath, frontmatter: parsed.data });
    }
  }
  return lessons;
}

export function getLessonBySlug(slug: string[]): { meta: LessonMeta; source: string } | null {
  const indexPath = path.join(CONTENT_ROOT, ...slug, "index.mdx");
  if (!fs.existsSync(indexPath)) return null;
  const raw = fs.readFileSync(indexPath, "utf8");
  const { data, content } = matter(raw);
  const parsed = frontmatterSchema.safeParse(data);
  if (!parsed.success) return null;
  return {
    meta: { slug, path: indexPath, frontmatter: parsed.data },
    source: content,
  };
}

export function groupByLayer(): ModuleGroup[] {
  const lessons = getAllLessons();
  const byLayer = new Map<string, ModuleGroup>();
  for (const l of lessons) {
    const layerSlug = l.slug[0];
    if (!byLayer.has(layerSlug)) {
      byLayer.set(layerSlug, {
        layerSlug,
        layer: l.frontmatter.layer,
        title: titleCase(layerSlug),
        lessons: [],
      });
    }
    byLayer.get(layerSlug)!.lessons.push(l);
  }
  for (const g of byLayer.values()) {
    g.lessons.sort((a, b) => a.frontmatter.order - b.frontmatter.order);
  }
  return [...byLayer.values()].sort((a, b) => a.layer - b.layer);
}

export function lessonHref(slug: string[]) {
  return "/learn/" + slug.join("/");
}

export function lessonTitle(slug: string[]) {
  return titleCase(slug[slug.length - 1]);
}
