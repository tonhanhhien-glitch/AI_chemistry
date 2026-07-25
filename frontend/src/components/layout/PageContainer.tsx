import type { ReactNode } from "react";
import Header from "./Header";
import Footer from "./Footer";

export default function PageContainer({ className, headerSearch, children }: { className?: string; headerSearch?: ReactNode; children: ReactNode }) {
  return <><Header search={headerSearch} /><main className={className ? `page-shell ${className}` : "page-shell"}>{children}</main><Footer /></>;
}
