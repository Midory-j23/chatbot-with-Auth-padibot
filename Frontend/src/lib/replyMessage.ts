export type ReplyTarget = {
  id: string | number;
  content: string;
  isUser: boolean;
};

const REPLY_START = "<<<REPLY>>>";
const REPLY_END = "<<<END_REPLY>>>";

/** Persist reply quote + message body in one DB string. */
export function encodeReplyMessage(
  message: string,
  replyTo: Pick<ReplyTarget, "content" | "isUser">,
): string {
  const role = replyTo.isUser ? "user" : "assistant";
  const quote = replyTo.content.trim().replace(/\r\n/g, "\n");
  return `${REPLY_START}${role}\n${quote}\n${REPLY_END}\n${message}`;
}

/** Parse stored message back into quote + body for UI. */
export function decodeReplyMessage(raw: string): {
  content: string;
  replyTo?: Pick<ReplyTarget, "content" | "isUser">;
} {
  if (!raw.startsWith(REPLY_START)) {
    return { content: raw };
  }

  const endIdx = raw.indexOf(`\n${REPLY_END}\n`);
  if (endIdx === -1) {
    return { content: raw };
  }

  const headerAndQuote = raw.slice(REPLY_START.length, endIdx);
  const content = raw.slice(endIdx + REPLY_END.length + 2);
  const nl = headerAndQuote.indexOf("\n");
  if (nl === -1) {
    return { content: raw };
  }

  const role = headerAndQuote.slice(0, nl).trim();
  const quote = headerAndQuote.slice(nl + 1).trim();

  return {
    content,
    replyTo: {
      content: quote,
      isUser: role === "user",
    },
  };
}

export function truncateQuote(text: string, max = 120): string {
  const clean = text.replace(/\s+/g, " ").trim();
  if (clean.length <= max) return clean;
  return `${clean.slice(0, max)}…`;
}
