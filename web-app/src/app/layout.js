import "./globals.css";

export const metadata = {
  title: "Ctrl+Eat",
  description: "Food recommendation app starter",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
