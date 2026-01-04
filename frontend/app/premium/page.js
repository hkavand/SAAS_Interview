import { redirect } from "next/navigation";
import axios from "axios";

export default async function PremiumPage() {
  let user;
  try {
    const res = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/me/`, { withCredentials: true });
    user = res.data;
  } catch {
    redirect("/login");
  }

  if (user.subscription_status !== "active") {
    redirect("/dashboard");
  }

  return <div>Welcome to Premium Content!</div>;
}
