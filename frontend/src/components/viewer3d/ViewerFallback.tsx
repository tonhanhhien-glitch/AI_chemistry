export default function ViewerFallback({ message = "Trình duyệt không thể khởi tạo WebGL. Bạn vẫn có thể học từ cấu trúc Lewis và bảng VSEPR." }: { message?: string }) {
  return <div className="viewer-fallback" role="status"><span aria-hidden="true">◌</span><p>{message}</p></div>;
}
