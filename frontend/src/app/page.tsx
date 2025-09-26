import { redirect } from 'next/navigation';

export default function Home() {
  // Redirect users hitting the Vercel root to the Django-rendered login page
  const base = process.env.NEXT_PUBLIC_API_URL ?? '';
  const target = base.endsWith('/') ? `${base}login/` : `${base}/login/`;
  redirect(target);
}
