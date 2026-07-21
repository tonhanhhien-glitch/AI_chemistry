import { NavLink } from "react-router-dom";

const links = [["/", "Trang chủ"], ["/analysis", "Phân tích"], ["/examples", "Ví dụ"], ["/rules", "Quy tắc VSEPR"], ["/survey", "Khảo sát"]];

export default function Header() {
  return <header className="site-header"><NavLink className="brand" to="/">VSEPR<span>Lab</span></NavLink><nav aria-label="Điều hướng chính">{links.map(([to, label]) => <NavLink key={to} to={to} className={({ isActive }) => isActive ? "active" : ""}>{label}</NavLink>)}</nav></header>;
}
