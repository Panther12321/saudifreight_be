frappe.pages["naqil-admin"].on_page_load = function (wrapper) {
  frappe.ui.make_app_page({ parent: wrapper, title: "إدارة ناقل", single_column: true });

  const html = `
    <div class="naqil-admin-shell" dir="rtl">
      <aside class="naqil-admin-sidebar" aria-label="قائمة إدارة ناقل">
        <div class="naqil-admin-brand">ناقل</div>
        <button class="naqil-admin-nav-item is-active" type="button" data-route="drivers"><span class="fa fa-users"></span><span>السائقين</span></button>
        <button class="naqil-admin-nav-item" type="button" data-route="customers"><span class="fa fa-building"></span><span>العملاء</span></button>
      </aside>
      <main class="naqil-admin-main">
        <span class="naqil-admin-eyebrow">إدارة ناقل</span>
        <h2>السائقين</h2>
        <div class="naqil-admin-content"><p>جارٍ تحميل طلبات السائقين...</p></div>
      </main>
    </div>`;

  const root = $(wrapper).find(".layout-main-section");
  root.html(html);
  const content = root.find(".naqil-admin-content");
  const escapeHtml = (value) => frappe.utils.escape_html(String(value || "—"));
  const displayDate = (value) => value ? frappe.datetime.str_to_user(value) : "غير محدد";
  const printDocument = (url) => {
    const printable = window.open(url, "_blank");
    if (!printable) {
      frappe.msgprint("يرجى السماح بالنوافذ المنبثقة لطباعة المستند.");
      return;
    }
    printable.addEventListener("load", () => printable.print(), { once: true });
  };

  const reviewApplicant = (organization, decision, reason, reviewMethod, applicantLabel, renderList) => {
    frappe.call({
      method: reviewMethod,
      args: { organization, decision, reason },
      freeze: true,
      freeze_message: "جارٍ حفظ القرار...",
    }).then(() => {
      frappe.show_alert({ message: decision === "approve" ? `تمت الموافقة على ${applicantLabel}` : "تم رفض الطلب", indicator: decision === "approve" ? "green" : "red" });
      renderList();
    });
  };

  const renderApplicant = (organization, options) => {
    content.html("<p>جارٍ تحميل ملف المتقدم...</p>");
    frappe.call({ method: options.getMethod, args: { organization } }).then((response) => {
      const data = response.message;
      const applicant = data.organization;
      const docs = data.documents || [];
      const docsHtml = docs.length ? docs.map((doc) => `
        <div class="naqil-document-row">
          <div><strong>${escapeHtml(doc.document_label)}</strong><br><span>ينتهي: ${displayDate(doc.expiry_date)}</span></div>
          <div class="naqil-document-actions"><span class="naqil-status">${escapeHtml(doc.status)}</span><a href="${encodeURI(doc.document_file)}" target="_blank" rel="noopener">فتح المستند</a><button class="btn btn-xs btn-default naqil-print-document" data-file="${encodeURI(doc.document_file)}">طباعة</button></div>
        </div>`).join("") : "<div class='naqil-empty-state'>لم يرفع المتقدم أي مستند حتى الآن.</div>";

      content.html(`
        <button class="btn btn-default naqil-back-button">عودة إلى الطلبات</button>
        <div class="naqil-applicant-header"><div><h3>${escapeHtml(applicant.organization_name)}</h3><p>${escapeHtml(applicant.name)}</p></div><span class="naqil-status">${escapeHtml(applicant.status)}</span></div>
        <section class="naqil-detail-card"><h4>بيانات ${options.applicantLabel}</h4><dl class="naqil-details-grid">
          <div><dt>الاسم</dt><dd>${escapeHtml(applicant.contact_name)}</dd></div><div><dt>الجوال</dt><dd>${escapeHtml(applicant.contact_phone)}</dd></div>
          ${options.isCarrier ? `<div><dt>الهوية</dt><dd>${escapeHtml(applicant.identity_number)}</dd></div><div><dt>انتهاء الهوية</dt><dd>${displayDate(applicant.identity_expiry_date)}</dd></div><div><dt>رخصة النقل</dt><dd>${escapeHtml(applicant.transport_license_number)}</dd></div><div><dt>انتهاء الرخصة</dt><dd>${displayDate(applicant.transport_license_expiry_date)}</dd></div><div><dt>المدينة</dt><dd>${escapeHtml(applicant.city)}</dd></div><div><dt>العنوان</dt><dd>${escapeHtml(applicant.address)}</dd></div>` : ""}
        </dl></section>
        <section class="naqil-detail-card"><h4>المستندات المرفوعة</h4>${docsHtml}</section>
        <section class="naqil-review-actions"><button class="btn btn-default naqil-print-profile">طباعة الملف</button><button class="btn btn-success naqil-approve">موافقة</button><button class="btn btn-danger naqil-reject">رفض</button></section>`);

      content.find(".naqil-back-button").on("click", options.renderList);
      content.find(".naqil-print-document").on("click", function () { printDocument($(this).data("file")); });
      content.find(".naqil-print-profile").on("click", () => window.print());
      content.find(".naqil-approve").on("click", () => frappe.confirm(`هل تؤكد الموافقة على ${options.applicantLabel}؟`, () => reviewApplicant(organization, "approve", "", options.reviewMethod, options.applicantLabel, options.renderList)));
      content.find(".naqil-reject").on("click", () => frappe.prompt([{ fieldname: "reason", fieldtype: "Small Text", label: "سبب الرفض", reqd: 1 }], (values) => reviewApplicant(organization, "reject", values.reason, options.reviewMethod, options.applicantLabel, options.renderList), "رفض الطلب", "تأكيد الرفض"));
    });
  };

  const renderApplicants = (options) => {
    root.find(".naqil-admin-main h2").text(options.heading);
    root.find(".naqil-admin-nav-item").removeClass("is-active");
    root.find(`[data-route='${options.route}']`).addClass("is-active");
    content.html(`<p>جارٍ تحميل طلبات ${options.pluralLabel}...</p>`);
    frappe.call({ method: options.listMethod }).then((response) => {
      const applicants = response.message || [];
      if (!applicants.length) {
        content.html(`<div class='naqil-empty-state'>لا توجد طلبات ${options.pluralLabel} جديدة للمراجعة.</div>`);
        return;
      }
      content.html(applicants.map((applicant) => `
        <button class="naqil-applicant-card" data-organization="${escapeHtml(applicant.name)}"><span><strong>${escapeHtml(applicant.organization_name)}</strong><small>${escapeHtml(applicant.contact_name)} · ${options.isCarrier ? escapeHtml(applicant.city) : escapeHtml(applicant.contact_phone)}</small></span><span>فتح الملف</span></button>`).join(""));
      content.find(".naqil-applicant-card").on("click", function () { renderApplicant($(this).data("organization"), options); });
    });
  };

  const driverOptions = { route: "drivers", heading: "السائقين", applicantLabel: "المتقدم", pluralLabel: "سائقين", isCarrier: true, listMethod: "naqil.api.list_carrier_applicants", getMethod: "naqil.api.get_carrier_applicant", reviewMethod: "naqil.api.review_carrier_applicant" };
  const customerOptions = { route: "customers", heading: "العملاء", applicantLabel: "العميل", pluralLabel: "عملاء", isCarrier: false, listMethod: "naqil.api.list_customer_applicants", getMethod: "naqil.api.get_customer_applicant", reviewMethod: "naqil.api.review_customer_applicant" };
  driverOptions.renderList = () => renderApplicants(driverOptions);
  customerOptions.renderList = () => renderApplicants(customerOptions);
  root.find("[data-route='drivers']").on("click", driverOptions.renderList);
  root.find("[data-route='customers']").on("click", customerOptions.renderList);
  driverOptions.renderList();

  root.append(`<style>
    .naqil-admin-shell{min-height:calc(100vh - 150px);display:flex;background:#f7f8fb;border:1px solid #e8ebf0;border-radius:16px;overflow:hidden}.naqil-admin-sidebar{width:240px;flex:0 0 240px;background:#061b3a;padding:26px 16px;color:#fff}.naqil-admin-brand{font-size:24px;font-weight:800;margin:0 10px 28px}.naqil-admin-nav-item{width:100%;display:flex;align-items:center;gap:12px;border:0;border-radius:10px;padding:13px 14px;color:#fff;background:transparent;font-size:16px;font-weight:700;text-align:right;cursor:pointer}.naqil-admin-nav-item+.naqil-admin-nav-item{margin-top:8px}.naqil-admin-nav-item.is-active,.naqil-admin-nav-item:hover{background:#ef8200}.naqil-admin-main{flex:1;padding:48px;color:#0a1d3a}.naqil-admin-eyebrow{color:#ef8200;font-weight:700}.naqil-admin-main h2{margin:12px 0 8px;font-size:32px;font-weight:800}.naqil-applicant-card{width:100%;display:flex;justify-content:space-between;align-items:center;border:1px solid #e0e6ef;border-radius:12px;background:#fff;padding:18px;margin-top:12px;text-align:right;color:#0a1d3a;cursor:pointer}.naqil-applicant-card:hover{border-color:#ef8200}.naqil-applicant-card small{display:block;color:#687386;margin-top:4px}.naqil-detail-card{background:#fff;border:1px solid #e0e6ef;border-radius:12px;padding:20px;margin-top:16px}.naqil-applicant-header{display:flex;justify-content:space-between;align-items:start;margin-top:20px}.naqil-applicant-header h3{margin:0;font-size:24px}.naqil-details-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin:0}.naqil-details-grid dt{color:#687386;font-size:13px}.naqil-details-grid dd{margin:4px 0 0;font-weight:700}.naqil-document-row{display:flex;justify-content:space-between;padding:13px 0;border-bottom:1px solid #edf0f4}.naqil-document-actions{display:flex;gap:14px;align-items:center}.naqil-status{padding:5px 9px;background:#fff3df;color:#945600;border-radius:999px;font-size:12px;font-weight:700}.naqil-review-actions{display:flex;gap:10px;margin-top:18px}.naqil-empty-state{border:1px dashed #cbd5e1;border-radius:12px;padding:24px;color:#687386;text-align:center}@media(max-width:640px){.naqil-admin-shell{flex-direction:column}.naqil-admin-sidebar{width:100%;flex-basis:auto}.naqil-admin-main{padding:30px 22px}.naqil-details-grid{grid-template-columns:1fr}}
  </style>`);
};
