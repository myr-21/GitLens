import type { Repo } from "@/components/RepoCard";

export const repos: Repo[] = [
  {
    slug: "lucide",
    name: "lucide-icons / lucide",
    description: "Beautiful & consistent icons made by the community. Fork of Feather Icons.",
    tags: ["SVG", "TypeScript", "React"],
    match: 98,
    health: "A+",
    rationale:
      "Highly active ecosystem with architectural patterns similar to your UI component libraries.",
  },
  {
    slug: "create-t3-app",
    name: "t3-oss / create-t3-app",
    description: "The best way to start a full-stack, typesafe Next.js app with ease.",
    tags: ["Next.js", "Prisma", "tRPC"],
    match: 92,
    health: "A",
    rationale:
      "Matches your preference for end-to-end typesafety and Next.js routing structures.",
  },
  {
    slug: "neon",
    name: "neondatabase / neon",
    description: "Serverless Postgres with storage/compute separation. Scales to zero automatically.",
    tags: ["Rust", "PostgreSQL", "Cloud"],
    match: 90,
    health: "A+",
    rationale:
      "Strong fit for your serverless-first infra searches and Postgres workflows.",
  },
  {
    slug: "tauri",
    name: "tauri-apps / tauri",
    description: "Build smaller, faster, and more secure desktop applications with a web frontend.",
    tags: ["Rust", "JavaScript", "Desktop"],
    match: 86,
    health: "A",
    rationale:
      "Pairs well with your Rust history. Lighter alternative to Electron-based projects.",
  },
  {
    slug: "fastapi",
    name: "tiangolo / fastapi",
    description: "Modern, fast (high-performance) web framework for Python based on standard type hints.",
    tags: ["Python", "ASGI", "OpenAPI"],
    match: 84,
    health: "A+",
    rationale: "Aligns with your microservice and async-first backend searches.",
  },
  {
    slug: "shadcn-ui",
    name: "shadcn-ui / ui",
    description: "Beautifully designed components built with Radix UI and Tailwind CSS.",
    tags: ["React", "Tailwind", "Radix"],
    match: 81,
    health: "S",
    rationale: "Architectural cousin to libraries you've already saved.",
  },
];

export function getRepo(slug: string) {
  return repos.find((r) => r.slug === slug);
}
