export interface Idea {
  id: number;
  text: string;
  votes: number;
  created_at: string;
}

const BASE = "/api";

async function asJson<T>(resp: Response): Promise<T> {
  if (!resp.ok) {
    throw new Error(`${resp.status} ${resp.statusText}`);
  }
  return resp.json() as Promise<T>;
}

/** Fetches all ideas, newest first. */
export function listIdeas(): Promise<Idea[]> {
  return fetch(`${BASE}/ideas`).then(asJson<Idea[]>);
}

/** Creates a new idea with the given text. */
export function createIdea(text: string): Promise<Idea> {
  return fetch(`${BASE}/ideas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  }).then(asJson<Idea>);
}

/** Upvotes the idea with the given id. */
export function upvoteIdea(id: number): Promise<Idea> {
  return fetch(`${BASE}/ideas/${id}/upvote`, { method: "POST" }).then(asJson<Idea>);
}
