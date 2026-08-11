/**
 * Split model output into reasoning vs user-facing answer.
 * Handles `<think>` and `` blocks (case-insensitive),
 * including tags split across streamed chunks.
 */

const TAG_SPECS: Array<{ open: string; close: string }> = [
  { open: "<think>", close: "</think>" },
  { open: "<think>", close: "</think>" },
];

function findPartialSuffix(text: string, target: string): number {
  const max = Math.min(text.length, target.length - 1);
  for (let len = max; len > 0; len--) {
    if (target.slice(0, len).toLowerCase() === text.slice(-len).toLowerCase()) {
      return text.length - len;
    }
  }
  return -1;
}

export class RedactedThinkingSplitter {
  private carry = "";
  thinking = "";
  answer = "";
  private inThinking = false;
  private closeTag = TAG_SPECS[0].close;

  push(chunk: string): { thinking: string; answer: string } {
    if (chunk) this.carry += chunk;
    this.drain(false);
    return { thinking: this.thinking, answer: this.answer };
  }

  finish(): { thinking: string; answer: string } {
    this.drain(true);
    return { thinking: this.thinking, answer: this.answer };
  }

  private drain(flush: boolean) {
    while (this.carry.length > 0) {
      if (!this.inThinking) {
        let matched = false;
        for (const spec of TAG_SPECS) {
          const lower = this.carry.toLowerCase();
          const openIdx = lower.indexOf(spec.open);
          if (openIdx >= 0) {
            this.answer += this.carry.slice(0, openIdx);
            this.carry = this.carry.slice(openIdx + spec.open.length);
            this.inThinking = true;
            this.closeTag = spec.close;
            matched = true;
            break;
          }
          const holdFrom = findPartialSuffix(this.carry, spec.open);
          if (holdFrom >= 0 && !flush) {
            this.answer += this.carry.slice(0, holdFrom);
            this.carry = this.carry.slice(holdFrom);
            matched = true;
            break;
          }
        }
        if (matched) continue;
        this.answer += this.carry;
        this.carry = "";
        break;
      }

      const lower = this.carry.toLowerCase();
      const closeIdx = lower.indexOf(this.closeTag);
      if (closeIdx >= 0) {
        this.thinking += this.carry.slice(0, closeIdx);
        this.carry = this.carry.slice(closeIdx + this.closeTag.length);
        this.inThinking = false;
        continue;
      }
      const holdFrom = findPartialSuffix(this.carry, this.closeTag);
      if (holdFrom >= 0 && !flush) {
        this.thinking += this.carry.slice(0, holdFrom);
        this.carry = this.carry.slice(holdFrom);
        break;
      }
      if (flush) {
        this.thinking += this.carry;
        this.carry = "";
        this.inThinking = false;
      } else {
        this.thinking += this.carry;
        this.carry = "";
      }
      break;
    }
  }
}

const BLOCK_RE =
  /<\s*(?:redacted_thinking|think)\s*>([\s\S]*?)<\s*\/\s*(?:redacted_thinking|think)\s*>/gi;

/** One-shot split for complete strings (e.g. API reload). */
export function splitRedactedThinking(raw: string): {
  thinking: string;
  answer: string;
} {
  const thinkingParts: string[] = [];
  let answer = raw ?? "";
  answer = answer.replace(BLOCK_RE, (_m, inner: string) => {
    thinkingParts.push(inner);
    return "";
  });
  const openRe = /<\s*(?:redacted_thinking|think)\s*>([\s\S]*)$/i;
  const open = answer.match(openRe);
  if (open) {
    thinkingParts.push(open[1]);
    answer = answer.slice(0, open.index);
  }
  return { thinking: thinkingParts.join("\n\n").trim(), answer: answer.trim() };
}

/** Remove leaked system/instruction text from the visible answer. */
export function stripInstructionLeaks(text: string): string {
  let t = (text ?? "").trim();
  if (!t) return t;

  t = t.replace(/\n*\[[^\]]*(?:فقط پاسخ|Reply with only|بدون استدلال|no reasoning)[^\]]*\]\s*$/gi, "");
  t = t.replace(/\n*\(لطفاً فقط[^\)]*\)\s*$/gi, "");
  t = t.replace(/\*?\s*But the instruction says[^*]*\*?/gi, "");
  t = t.replace(/:Me:|:\s*My response:/gi, "");
  t = t.replace(/\*+\s*$/g, "").trim();
  return t;
}

/** Full pipeline: split thinking tags, then clean instruction leaks from answer. */
export function parseModelOutput(raw: string): {
  thinking: string;
  answer: string;
} {
  const { thinking, answer } = splitRedactedThinking(raw);
  return {
    thinking: thinking.trim(),
    answer: stripInstructionLeaks(answer),
  };
}
