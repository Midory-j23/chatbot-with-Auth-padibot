const PERSIAN_ARABIC = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/;
const LATIN = /[A-Za-z]/;

export function isPersianText(text: string): boolean {
  const trimmed = text.trim();
  if (!trimmed) return false;

  let persian = 0;
  let latin = 0;

  for (const char of trimmed) {
    if (PERSIAN_ARABIC.test(char)) persian++;
    else if (LATIN.test(char)) latin++;
  }

  if (persian === 0) return false;
  return persian >= latin;
}

export function getMessageTextAlign(text: string): "text-right" | "text-left" {
  return isPersianText(text) ? "text-right" : "text-left";
}
