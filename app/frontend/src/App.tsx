import { useEffect, useState } from "react";

import { createIdea, Idea, listIdeas, upvoteIdea } from "./api";

export default function App() {
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);

  function refresh() {
    listIdeas()
      .then(setIdeas)
      .catch((err: Error) => setError(err.message));
  }

  useEffect(refresh, []);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!draft.trim()) return;
    createIdea(draft.trim())
      .then(() => {
        setDraft("");
        refresh();
      })
      .catch((err: Error) => setError(err.message));
  }

  function handleUpvote(id: number) {
    upvoteIdea(id)
      .then(refresh)
      .catch((err: Error) => setError(err.message));
  }

  return (
    <main style={{ maxWidth: 480, margin: "2rem auto", fontFamily: "sans-serif" }}>
      <h1>Idea Board</h1>

      <form onSubmit={handleSubmit}>
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="What's the idea?"
          style={{ width: "70%" }}
        />
        <button type="submit">Add</button>
      </form>

      {error && <p style={{ color: "crimson" }}>{error}</p>}

      <ul style={{ listStyle: "none", padding: 0 }}>
        {ideas.map((idea) => (
          <li key={idea.id} style={{ margin: "0.5rem 0" }}>
            <button onClick={() => handleUpvote(idea.id)}>▲ {idea.votes}</button>
            {" "}
            {idea.text}
          </li>
        ))}
      </ul>
    </main>
  );
}
