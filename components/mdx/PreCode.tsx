import { highlight } from "@/lib/shiki";
import { CodeBlock } from "@/components/CodeBlock";

// MDX renders ```lang blocks as <pre><code class="language-lang">…</code></pre>.
// Our custom `pre` receives a child <code> with className + string children.
export async function Pre({ children }: { children: any }) {
  const codeEl = children?.props ? children : null;
  const raw: string = codeEl?.props?.children ?? "";
  const className: string = codeEl?.props?.className ?? "";
  const lang = /language-([\w-]+)/.exec(className)?.[1] ?? "text";
  const meta: string = codeEl?.props?.meta ?? "";

  const colabMatch = /colab=([^\s]+)/.exec(meta);
  const fileMatch = /file=([^\s]+)/.exec(meta);

  const html = await highlight(raw.replace(/\n$/, ""), lang);
  return (
    <CodeBlock
      html={html}
      raw={raw}
      lang={lang}
      colabPath={colabMatch?.[1]}
      filename={fileMatch?.[1]}
    />
  );
}
