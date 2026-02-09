export async function askOllama(prompt: string) {
  const res = await fetch("http://localhost:3001/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ prompt }),
  });

  if (!res.ok) {
    throw new Error("Backend error");
  }

  const data = await res.json();
  return data.response as string;
}
