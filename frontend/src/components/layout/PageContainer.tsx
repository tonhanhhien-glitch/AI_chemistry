import type { ReactNode } from "react";
import Header from "./Header";
import Footer from "./Footer";

export default function PageContainer({ children }: { children: ReactNode }) {
  return <><Header /><main className="page-shell">{children}</main><Footer /></>;
}
