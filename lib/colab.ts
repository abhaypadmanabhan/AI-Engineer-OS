const GH_USER = process.env.NEXT_PUBLIC_GH_USER ?? "your-handle";
const GH_REPO = process.env.NEXT_PUBLIC_GH_REPO ?? "ai-engineer-os";
const GH_BRANCH = process.env.NEXT_PUBLIC_GH_BRANCH ?? "main";

export function colabUrl(notebookPath: string) {
  const clean = notebookPath.replace(/^\//, "");
  return `https://colab.research.google.com/github/${GH_USER}/${GH_REPO}/blob/${GH_BRANCH}/${clean}`;
}
