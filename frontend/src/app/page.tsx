import { redirect } from 'next/navigation';

function normalizeBaseUrl(value: string | undefined): string {
  if (!value) return '';
  let url = value.trim();
  // Prepend https:// if protocol is missing
  if (!/^https?:\/\//i.test(url)) {
    url = `https://${url}`;
  }
  // Remove trailing slashes
  url = url.replace(/\/+$/, '');
  return url;
}

export default function Home() {
  const base = normalizeBaseUrl(process.env.NEXT_PUBLIC_API_URL);
  const target = base ? `${base}/login/` : '/';
  redirect(target);
}
