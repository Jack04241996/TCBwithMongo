export function controlNavbarLinks() {
  const token = localStorage.getItem("token");
  if (!token) return; // 沒登入就不顯示

  try {
    const payload = JSON.parse(atob(token.split(".")[1])); // 直接解 JWT
    const level = Number(payload.level || 0);

    if (level > 1) {
      document.getElementById("users_management")?.removeAttribute("hidden");
      document.getElementById("products_management")?.removeAttribute("hidden");
    }
  } catch (err) {
    console.error("JWT 解析失敗", err);
  }
}