frappe.pages["naqil-admin"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "إدارة ناقل",
    single_column: true,
  });

  const content = `
    <div class="naqil-admin-shell" dir="rtl">
      <aside class="naqil-admin-sidebar" aria-label="قائمة إدارة ناقل">
        <div class="naqil-admin-brand">ناقل</div>
        <button class="naqil-admin-nav-item is-active" type="button" data-route="drivers">
          <span class="fa fa-users"></span>
          <span>السائقين</span>
        </button>
      </aside>
      <main class="naqil-admin-main">
        <span class="naqil-admin-eyebrow">إدارة ناقل</span>
        <h2>السائقين</h2>
        <p>هنا ستظهر طلبات السائقين المسجلين للمراجعة عند إضافتها لاحقاً.</p>
      </main>
    </div>
  `;

  $(wrapper).find(".layout-main-section").html(content);
  $(wrapper).find("[data-route='drivers']").on("click", () => {
    frappe.set_route("List", "Naqil Organization", { organization_type: "Carrier" });
  });

  $(wrapper).find(".layout-main-section").append(`
    <style>
      .naqil-admin-shell { min-height: calc(100vh - 150px); display: flex; background: #f7f8fb; border: 1px solid #e8ebf0; border-radius: 16px; overflow: hidden; }
      .naqil-admin-sidebar { width: 240px; flex: 0 0 240px; background: #061b3a; padding: 26px 16px; color: #fff; }
      .naqil-admin-brand { font-size: 24px; font-weight: 800; margin: 0 10px 28px; }
      .naqil-admin-nav-item { width: 100%; display: flex; align-items: center; gap: 12px; border: 0; border-radius: 10px; padding: 13px 14px; color: #fff; background: #ef8200; font-size: 16px; font-weight: 700; text-align: right; cursor: pointer; }
      .naqil-admin-main { flex: 1; padding: 48px; color: #0a1d3a; }
      .naqil-admin-eyebrow { color: #ef8200; font-weight: 700; }
      .naqil-admin-main h2 { margin: 12px 0 8px; font-size: 32px; font-weight: 800; }
      .naqil-admin-main p { color: #687386; font-size: 16px; }
      @media (max-width: 640px) { .naqil-admin-shell { flex-direction: column; } .naqil-admin-sidebar { width: 100%; flex-basis: auto; } .naqil-admin-main { padding: 30px 22px; } }
    </style>
  `);
};
