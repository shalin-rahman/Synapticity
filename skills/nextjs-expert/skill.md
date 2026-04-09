# Skill: Next.js Expert (Architect Level)
# Usage: Use when building or refactoring modern Next.js applications (v14/v15).

## Core Directives:
- **Architecture:** Default to the **App Router** architecture. Prioritize **React Server Components (RSC)** for data fetching and only use `"use client"` for interactive leaf components.
- **Data Fetching:** Leverage standard `async/await` fetch in RSC. Use `revalidatePath` and `revalidateTag` for on-demand cache invalidation.
- **TypeScript:** Enforce strict typing. Use `NextPage`, `Metadata`, and `APIRoute` types where applicable.
- **Styling:** Default to **Tailwind CSS**. Use `lucide-react` for icons and `shadcn/ui` patterns for high-quality accessible components.
- **Optimization:** Prioritize Image optimization (`next/image`), Font optimization (`next/font`), and Script optimization. Maximize Core Web Vitals (LCP, FID, CLS).

## High-Quality Pattern: Server Action
```typescript
"use server"

import { revalidatePath } from "next/cache"

export async function updateItem(id: string, formData: FormData) {
  const data = Object.fromEntries(formData)
  await db.item.update({ where: { id }, data })
  revalidatePath("/dashboard")
}
```

## Guardrails:
- No `pages/` directory unless legacy support is explicitly requested.
- Avoid generic `try/catch` in components; use **Error Boundaries** (`error.tsx`).
- Never expose environment variables without the `NEXT_PUBLIC_` prefix (and only when safe).
