import type { Metadata } from "next";
import "./globals.css";
import Nav from "@/components/Nav";

export const metadata: Metadata = {
  title: "AI Content Studio",
  description: "Duyệt và đăng gói nội dung mỗi ngày",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>
        <Nav />
        {children}
      </body>
    </html>
  );
}
