import type { VseprResult } from "../../types/vsepr";

export default function ElectronDomainTable({ result }: { result: VseprResult }) {
  return <div className="domain-grid"><div><span>Miền liên kết</span><strong>{result.bonding_domains}</strong></div><div><span>Cặp e tự do</span><strong>{result.lone_pair_domains}</strong></div><div><span>Số miền tổng</span><strong>{result.steric_number}</strong></div></div>;
}
