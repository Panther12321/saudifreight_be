(() => {
  const addDriversMenu = () => {
    if (document.querySelector("#naqil-drivers-menu")) return;

    const sidebar = document.querySelector(".standard-sidebar-section") || document.querySelector(".desk-sidebar");
    if (!sidebar) {
      window.setTimeout(addDriversMenu, 250);
      return;
    }

    const menu = document.createElement("div");
    menu.id = "naqil-drivers-menu";
    menu.className = "standard-sidebar-item naqil-drivers-menu";
    menu.innerHTML = `
      <a class="standard-sidebar-item-link" href="/app/naqil-organization?organization_type=Carrier">
        <span class="sidebar-item-label">السائقين</span>
      </a>
    `;
    sidebar.prepend(menu);
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", addDriversMenu);
  } else {
    addDriversMenu();
  }
  frappe.after_ajax(addDriversMenu);
})();
