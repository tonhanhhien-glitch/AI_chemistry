// Bilingual UI string catalogue for the VSEPRLab frontend.
// Vietnamese is the source language (`vi`); English (`en`) is the parallel translation.
// Keys are flat, dot-namespaced strings. Use `translate(lang, key, params)` to resolve.

export type Lang = "vi" | "en";

export const LANGUAGES: Lang[] = ["vi", "en"];
export const DEFAULT_LANG: Lang = "vi";

type Catalogue = Record<string, string>;

const vi: Catalogue = {
  // Navigation & language toggle
  "nav.home": "Trang chủ",
  "nav.analysis": "Phân tích",
  "nav.examples": "Ví dụ",
  "nav.rules": "Quy tắc VSEPR",
  "nav.survey": "Khảo sát",
  "nav.ariaMain": "Điều hướng chính",
  "lang.toggleAria": "Đổi ngôn ngữ",
  "lang.switchTo": "English",

  // Footer
  "footer.tagline": "Công cụ học tập Lewis–VSEPR bằng quy tắc xác định.",
  "footer.note": "Giải thích AI chỉ diễn giải dữ kiện đã kiểm tra; mô hình 3D dự phòng có tính minh hoạ.",

  // Home page
  "home.hero.eyebrow": "Học Lewis · hiểu hình học",
  "home.hero.titlePrefix": "Từ công thức đến ",
  "home.hero.titleEm": "hình dạng phân tử",
  "home.hero.lede": "Một quy trình tiếng Việt nối cấu trúc Lewis, miền electron, AXnEm, VSEPR và mô hình 3D. Kết luận hoá học đến từ bộ quy tắc xác định — AI chỉ giải thích.",
  "home.hero.visualAria": "Minh hoạ hình học phân tử",
  "home.trust.offline": "hoạt động offline với bộ ví dụ",
  "home.trust.axTypes": "kiểu AXnEm từ 2–6 miền",
  "home.trust.noLlm": "kết luận hoá học do LLM tự quyết",
  "home.quickStart.eyebrow": "Bắt đầu nhanh",
  "home.quickStart.title": "Chất tiêu biểu",
  "home.quickStart.seeAll": "Xem tất cả →",
  "home.quickStart.empty": "Khởi động backend để tải bộ ví dụ đã tuyển chọn.",
  "home.scope.title": "Phạm vi có chủ đích",
  "home.scope.body": "Hỗ trợ phân tử và ion nhóm chính có mô hình Lewis/VSEPR rõ ràng, số miền ≤ 6. Không suy đoán đồng phân chỉ từ công thức, không xử lý phức kim loại chuyển tiếp, hydrate, ngoặc hoặc hệ số trong MVP.",

  // Formula input
  "formulaInput.label": "Công thức hoặc tên chất",
  "formulaInput.placeholder": "Ví dụ: H2O, XeF4, NO3-",
  "formulaInput.analyzing": "Đang phân tích…",
  "formulaInput.analyze": "Phân tích",
  "formulaInput.help": "Chỉ hỗ trợ công thức phẳng; ngoặc, hệ số, hydrate và kim loại chuyển tiếp chưa được hỗ trợ.",

  // Analysis page
  "analysis.eyebrow": "Phòng học phân tử",
  "analysis.title": "Phân tích từng bước",
  "analysis.intro": "Kiểm tra từng lớp biểu diễn, từ electron hoá trị đến mô hình không gian.",
  "analysis.error.empty": "Vui lòng nhập công thức hoặc tên chất.",
  "analysis.error.multi": "Có nhiều kết quả. Hãy nhập công thức hoặc tên đầy đủ hơn.",
  "analysis.error.notFound": "Không tìm thấy chất đã tuyển chọn phù hợp.",
  "analysis.error.searchFail": "Không thể tìm tên chất. Hãy thử nhập công thức.",
  "analysis.chooseStructure": "Chọn cấu tạo:",
  "analysis.retry": "Thử lại",
  "analysis.loading": "Đang chạy bộ quy tắc và dựng mô hình…",
  "analysis.step.lewis": "Cấu trúc Lewis",
  "analysis.step.domains": "Miền electron & AXnEm",
  "analysis.step.model3d": "Mô hình 3D tương tác",
  "analysis.step.properties": "Tính chất & nguồn",
  "analysis.step.explanation": "Giải thích sư phạm",
  "analysis.step.feedback": "Phản hồi ẩn danh",

  // Examples page
  "examples.loadError": "Không tải được ví dụ. Hãy kiểm tra backend.",
  "examples.eyebrow": "Thư viện tuyển chọn",
  "examples.title": "Ví dụ theo hình học",
  "examples.intro": "Nhấn một chất để chạy toàn bộ quy trình phân tích offline.",

  // Rules page
  "rules.loadError": "Không tải được bảng quy tắc.",
  "rules.eyebrow": "Bảng tra cứu",
  "rules.title": "Quy tắc VSEPR",
  "rules.intro": "Mỗi liên kết đơn, đôi hoặc ba tính là một miền electron quanh nguyên tử trung tâm.",
  "rules.bondingDomains": "miền liên kết",
  "rules.lonePairs": "cặp tự do",
  "rules.electronDomain": "Miền electron",
  "rules.molecular": "Phân tử",
  "rules.angle": "Góc",
  "rules.example": "Ví dụ",
  "rules.footnote": "Các nhãn sp³d/sp³d² nếu xuất hiện chỉ là gần đúng sư phạm kiểu VSEPR, không phải mô tả liên kết hiện đại đầy đủ.",

  // Geometry names (keyed by the backend English geometry string)
  "geometry.linear": "thẳng",
  "geometry.bent": "gấp khúc",
  "geometry.tetrahedral": "tứ diện",
  "geometry.trigonal planar": "tam giác phẳng",
  "geometry.trigonal pyramidal": "chóp tam giác",
  "geometry.trigonal bipyramidal": "lưỡng tháp tam giác",
  "geometry.seesaw": "bập bênh",
  "geometry.T-shaped": "chữ T",
  "geometry.octahedral": "bát diện",
  "geometry.square pyramidal": "chóp vuông",
  "geometry.square planar": "vuông phẳng",

  // VSEPR teaching notes (keyed by AXnEm), sourced from the backend rule table
  "rules.teachingNote.AX2": "Hai miền electron đẩy nhau về hai phía đối diện.",
  "rules.teachingNote.AX3": "Ba miền electron nằm trong cùng một mặt phẳng.",
  "rules.teachingNote.AX2E": "Một cặp electron tự do nén góc liên kết.",
  "rules.teachingNote.AX4": "Bốn miền liên kết hướng về bốn đỉnh tứ diện.",
  "rules.teachingNote.AX3E": "Cặp electron tự do chiếm một đỉnh tứ diện và nén góc.",
  "rules.teachingNote.AX2E2": "Hai cặp electron tự do làm góc liên kết nhỏ hơn góc tứ diện.",
  "rules.teachingNote.AX5": "Có ba vị trí xích đạo và hai vị trí trục.",
  "rules.teachingNote.AX4E": "Cặp tự do ưu tiên vị trí xích đạo.",
  "rules.teachingNote.AX3E2": "Hai cặp tự do ưu tiên hai vị trí xích đạo.",
  "rules.teachingNote.AX2E3": "Ba cặp tự do chiếm các vị trí xích đạo.",
  "rules.teachingNote.AX6": "Sáu miền liên kết phân bố theo bát diện.",
  "rules.teachingNote.AX5E": "Một cặp tự do chiếm một đỉnh bát diện.",
  "rules.teachingNote.AX4E2": "Hai cặp tự do nằm đối diện nhau.",

  // Survey page
  "survey.eyebrow": "Nghiên cứu giáo dục",
  "survey.title": "Khảo sát ẩn danh",
  "survey.intro": "Không thu tên, mã sinh viên hoặc email. Chỉ lưu mã phiên ngẫu nhiên, giai đoạn và câu trả lời cần thiết.",
  "survey.consent.title": "Thông tin đồng thuận & quyền riêng tư",
  "survey.consent.body": "Tham gia là tự nguyện. Bạn có thể dừng trước khi gửi. Dữ liệu dùng để đánh giá hiệu quả học tập và giáo viên chỉ xuất qua token bảo vệ.",
  "survey.consent.checkbox": "Tôi đã đọc và đồng ý tham gia ẩn danh.",
  "survey.phase.label": "Giai đoạn",
  "survey.phase.pre": "Bài kiểm tra trước",
  "survey.phase.post": "Bài kiểm tra sau",
  "survey.phase.likert": "Thang Likert trải nghiệm",
  "survey.q1": "Tôi tự tin đếm miền electron",
  "survey.q2": "Tôi tự tin suy ra hình học phân tử",
  "survey.submitting": "Đang gửi…",
  "survey.submit": "Gửi khảo sát ẩn danh",
  "survey.consentRequired": "Cần đánh dấu đồng thuận trước khi gửi.",

  // Not found page
  "notFound.eyebrow": "Lỗi 404",
  "notFound.title": "Không tìm thấy trang",
  "notFound.body": "Đường dẫn này không tồn tại hoặc đã thay đổi.",
  "notFound.home": "Về trang chủ",

  // AI disclaimer & explanation
  "explanation.disclaimer.claude": "Claude đã diễn giải",
  "explanation.disclaimer.deterministic": "Bản giải thích xác định",
  "explanation.disclaimer.body": "· Các kết luận Lewis, AXnEm, hình học và góc đến từ bộ quy tắc và không thể bị AI thay đổi.",
  "explanation.level.legend": "Mức độ giải thích",
  "explanation.level.basic": "Cơ bản",
  "explanation.level.intermediate": "Trung cấp",
  "explanation.level.advanced": "Nâng cao",
  "explanation.section.lewis": "Cấu trúc Lewis",
  "explanation.section.ax_en": "Phân loại AXnEm",
  "explanation.section.electron_geometry": "Hình học miền electron",
  "explanation.section.molecular_geometry": "Hình học phân tử",
  "explanation.section.structure_property": "Liên hệ cấu trúc – tính chất",
  "explanation.section.learning_tip": "Mẹo học",
  "explanation.section.disclaimer": "Lưu ý",
  "explanation.empty": "Chưa tạo giải thích. Nhấn nút để dùng dữ kiện đã kiểm tra.",
  "explanation.generate": "Tạo giải thích",
  "explanation.generating": "Đang tạo…",
  "explanation.regenerate": "Tạo lại",
  "explanation.copy": "Sao chép",

  // Feedback
  "feedback.errorReport.summary": "Báo cáo nghi ngờ sai hoá học",
  "feedback.errorReport.body": "Chọn “Nghi ngờ lỗi hoá học” và mô tả chính xác nguyên tử, điện tích hoặc góc cần kiểm tra.",
  "feedback.categoryLabel": "Loại phản hồi",
  "feedback.category.usefulness": "Mức hữu ích",
  "feedback.category.clarity": "Độ rõ ràng",
  "feedback.category.chemistryError": "Nghi ngờ lỗi hoá học",
  "feedback.category.other": "Khác",
  "feedback.commentLabel": "Ghi chú (không nhập tên hoặc mã sinh viên)",
  "feedback.submitting": "Đang gửi…",
  "feedback.submit": "Gửi phản hồi ẩn danh",
  "feedback.rating.legend": "Mức hữu ích (1–5)",

  // Molecule search
  "moleculeSearch.label": "Tìm theo tên hoặc công thức",
  "moleculeSearch.placeholder": "Nhập ít nhất 2 ký tự",

  // Lewis
  "lewis.formalCharge.caption": "Điện tích hình thức theo nguyên tử",
  "lewis.formalCharge.atom": "Nguyên tử",
  "lewis.formalCharge.lonePairs": "Cặp e tự do",
  "lewis.formalCharge.charge": "Điện tích",
  "lewis.svgAria": "Công thức Lewis",
  "lewis.totalValence": "Tổng electron hoá trị",
  "lewis.source": "Nguồn cấu trúc",
  "lewis.showFormalCharge": "Xem điện tích hình thức",
  "lewis.resonance.forms": "{forms} công thức cộng hưởng tương đương",

  // Properties
  "property.source.curated": "Dữ liệu tuyển chọn",
  "property.source.computed": "Giá trị tính toán",
  "property.source.pubchem": "Tham chiếu PubChem",
  "pubchem.title": "Tham chiếu cấu trúc",
  "pubchem.noCid": "Chưa gắn CID vì chưa hoàn tất xác minh nguồn. Không có dữ liệu giả được hiển thị.",
  "teachingNote.title": "Mẹo học",

  // 3D viewer
  "viewer3d.atomLabels": "Nhãn nguyên tử",
  "viewer3d.viewerAria": "Mô hình phân tử 3D tương tác",
  "viewer3d.help": "Kéo để xoay · cuộn/chụm để thu phóng · hỗ trợ cảm ứng.",
  "viewer3d.styleLabel": "Kiểu hiển thị",
  "viewer3d.style.stick": "Cầu và que",
  "viewer3d.style.sphere": "Lấp đầy không gian",
  "viewer3d.fallback": "Trình duyệt không thể khởi tạo WebGL. Bạn vẫn có thể học từ cấu trúc Lewis và bảng VSEPR.",
  "viewer3d.reset": "Đặt lại",
  "viewer3d.fullscreen": "Toàn màn hình",

  // VSEPR
  "vsepr.badgeAria": "Ký hiệu VSEPR {notation}",
  "vsepr.domain.bonding": "Miền liên kết",
  "vsepr.domain.lonePairs": "Cặp e tự do",
  "vsepr.domain.steric": "Số miền tổng",
  "vsepr.notationHint": "Đếm miền quanh nguyên tử trung tâm; liên kết bội vẫn là một miền.",
  "vsepr.electronGeometry": "Hình học miền electron",
  "vsepr.molecularGeometry": "Hình học phân tử",
  "vsepr.pedagogicalLabel": "Nhãn sư phạm:",

  // Workflow
  "workflow.summary.substance": "Chất",
  "workflow.summary.classification": "Phân loại",
  "workflow.summary.geometry": "Hình học",
  "workflow.summary.bonds": "liên kết",
  "workflow.summary.lonePairs": "cặp tự do",
  "workflow.stepper.aria": "Quy trình phân tích",
  "workflow.step.input": "Nhập chất",
  "workflow.step.lewis": "Lewis",
  "workflow.step.axen": "AXnEm",
  "workflow.step.geometry": "Hình học",
  "workflow.step.model3d": "Mô hình 3D",
  "workflow.step.explanation": "Giải thích",

  // API errors
  "api.error.timeout": "Yêu cầu đã hết thời gian chờ. Vui lòng thử lại.",
  "api.error.network": "Không thể kết nối tới máy chủ. Các ví dụ cần backend chạy cục bộ.",
};

const en: Catalogue = {
  // Navigation & language toggle
  "nav.home": "Home",
  "nav.analysis": "Analysis",
  "nav.examples": "Examples",
  "nav.rules": "VSEPR rules",
  "nav.survey": "Survey",
  "nav.ariaMain": "Main navigation",
  "lang.toggleAria": "Switch language",
  "lang.switchTo": "Tiếng Việt",

  // Footer
  "footer.tagline": "A Lewis–VSEPR learning tool driven by deterministic rules.",
  "footer.note": "The AI explanation only interprets verified facts; the fallback 3D model is illustrative.",

  // Home page
  "home.hero.eyebrow": "Learn Lewis · understand geometry",
  "home.hero.titlePrefix": "From formula to ",
  "home.hero.titleEm": "molecular shape",
  "home.hero.lede": "A workflow that links Lewis structures, electron domains, AXnEm, VSEPR and a 3D model. The chemistry conclusions come from a deterministic rule set — the AI only explains.",
  "home.hero.visualAria": "Molecular geometry illustration",
  "home.trust.offline": "works offline with the example set",
  "home.trust.axTypes": "AXnEm types from 2–6 domains",
  "home.trust.noLlm": "chemistry conclusions decided by the LLM",
  "home.quickStart.eyebrow": "Quick start",
  "home.quickStart.title": "Representative molecules",
  "home.quickStart.seeAll": "See all →",
  "home.quickStart.empty": "Start the backend to load the curated example set.",
  "home.scope.title": "Deliberate scope",
  "home.scope.body": "Supports main-group molecules and ions with a clear Lewis/VSEPR model and ≤ 6 domains. It does not infer isomers from the formula alone, and does not handle transition-metal complexes, hydrates, parentheses or coefficients in the MVP.",

  // Formula input
  "formulaInput.label": "Formula or substance name",
  "formulaInput.placeholder": "e.g. H2O, XeF4, NO3-",
  "formulaInput.analyzing": "Analyzing…",
  "formulaInput.analyze": "Analyze",
  "formulaInput.help": "Only flat formulas are supported; parentheses, coefficients, hydrates and transition metals are not yet supported.",

  // Analysis page
  "analysis.eyebrow": "Molecule lab",
  "analysis.title": "Step-by-step analysis",
  "analysis.intro": "Inspect each representation layer, from valence electrons to the spatial model.",
  "analysis.error.empty": "Please enter a formula or substance name.",
  "analysis.error.multi": "Multiple results found. Please enter a more complete formula or name.",
  "analysis.error.notFound": "No matching curated substance found.",
  "analysis.error.searchFail": "Could not look up the substance name. Try entering a formula.",
  "analysis.chooseStructure": "Choose a structure:",
  "analysis.retry": "Retry",
  "analysis.loading": "Running the rule set and building the model…",
  "analysis.step.lewis": "Lewis structure",
  "analysis.step.domains": "Electron domains & AXnEm",
  "analysis.step.model3d": "Interactive 3D model",
  "analysis.step.properties": "Properties & sources",
  "analysis.step.explanation": "Pedagogical explanation",
  "analysis.step.feedback": "Anonymous feedback",

  // Examples page
  "examples.loadError": "Could not load examples. Please check the backend.",
  "examples.eyebrow": "Curated library",
  "examples.title": "Examples by geometry",
  "examples.intro": "Click a substance to run the full offline analysis workflow.",

  // Rules page
  "rules.loadError": "Could not load the rules table.",
  "rules.eyebrow": "Reference table",
  "rules.title": "VSEPR rules",
  "rules.intro": "Each single, double or triple bond counts as one electron domain around the central atom.",
  "rules.bondingDomains": "bonding domains",
  "rules.lonePairs": "lone pairs",
  "rules.electronDomain": "Electron domains",
  "rules.molecular": "Molecular",
  "rules.angle": "Angle",
  "rules.example": "Examples",
  "rules.footnote": "Any sp³d/sp³d² labels shown are only a VSEPR-style pedagogical approximation, not a full modern description of bonding.",

  // Geometry names (keyed by the backend English geometry string)
  "geometry.linear": "linear",
  "geometry.bent": "bent",
  "geometry.tetrahedral": "tetrahedral",
  "geometry.trigonal planar": "trigonal planar",
  "geometry.trigonal pyramidal": "trigonal pyramidal",
  "geometry.trigonal bipyramidal": "trigonal bipyramidal",
  "geometry.seesaw": "seesaw",
  "geometry.T-shaped": "T-shaped",
  "geometry.octahedral": "octahedral",
  "geometry.square pyramidal": "square pyramidal",
  "geometry.square planar": "square planar",

  // VSEPR teaching notes (keyed by AXnEm), sourced from the backend rule table
  "rules.teachingNote.AX2": "Two electron domains repel to opposite sides.",
  "rules.teachingNote.AX3": "Three electron domains lie in the same plane.",
  "rules.teachingNote.AX2E": "One lone pair compresses the bond angle.",
  "rules.teachingNote.AX4": "Four bonding domains point to the four vertices of a tetrahedron.",
  "rules.teachingNote.AX3E": "The lone pair occupies one tetrahedral vertex and compresses the angle.",
  "rules.teachingNote.AX2E2": "Two lone pairs make the bond angle smaller than the tetrahedral angle.",
  "rules.teachingNote.AX5": "There are three equatorial and two axial positions.",
  "rules.teachingNote.AX4E": "The lone pair prefers an equatorial position.",
  "rules.teachingNote.AX3E2": "Two lone pairs prefer two equatorial positions.",
  "rules.teachingNote.AX2E3": "Three lone pairs occupy the equatorial positions.",
  "rules.teachingNote.AX6": "Six bonding domains are distributed over an octahedron.",
  "rules.teachingNote.AX5E": "One lone pair occupies one octahedral vertex.",
  "rules.teachingNote.AX4E2": "Two lone pairs lie opposite each other.",

  // Survey page
  "survey.eyebrow": "Educational research",
  "survey.title": "Anonymous survey",
  "survey.intro": "We do not collect names, student IDs or emails. Only a random session ID, phase and the necessary answers are stored.",
  "survey.consent.title": "Consent & privacy information",
  "survey.consent.body": "Participation is voluntary. You may stop before submitting. The data is used to evaluate learning effectiveness, and teachers can only export it through a protected token.",
  "survey.consent.checkbox": "I have read and agree to participate anonymously.",
  "survey.phase.label": "Phase",
  "survey.phase.pre": "Pre-test",
  "survey.phase.post": "Post-test",
  "survey.phase.likert": "Experience Likert scale",
  "survey.q1": "I am confident counting electron domains",
  "survey.q2": "I am confident deducing molecular geometry",
  "survey.submitting": "Submitting…",
  "survey.submit": "Submit anonymous survey",
  "survey.consentRequired": "You must check consent before submitting.",

  // Not found page
  "notFound.eyebrow": "Error 404",
  "notFound.title": "Page not found",
  "notFound.body": "This path does not exist or has changed.",
  "notFound.home": "Back to home",

  // AI disclaimer & explanation
  "explanation.disclaimer.claude": "Interpreted by Claude",
  "explanation.disclaimer.deterministic": "Deterministic explanation",
  "explanation.disclaimer.body": "· The Lewis, AXnEm, geometry and angle conclusions come from the rule set and cannot be changed by the AI.",
  "explanation.level.legend": "Explanation level",
  "explanation.level.basic": "Basic",
  "explanation.level.intermediate": "Intermediate",
  "explanation.level.advanced": "Advanced",
  "explanation.section.lewis": "Lewis structure",
  "explanation.section.ax_en": "AXnEm classification",
  "explanation.section.electron_geometry": "Electron-domain geometry",
  "explanation.section.molecular_geometry": "Molecular geometry",
  "explanation.section.structure_property": "Structure–property relationship",
  "explanation.section.learning_tip": "Learning tip",
  "explanation.section.disclaimer": "Note",
  "explanation.empty": "No explanation generated yet. Press the button to use the verified facts.",
  "explanation.generate": "Generate explanation",
  "explanation.generating": "Generating…",
  "explanation.regenerate": "Regenerate",
  "explanation.copy": "Copy",

  // Feedback
  "feedback.errorReport.summary": "Report a suspected chemistry error",
  "feedback.errorReport.body": "Choose “Suspected chemistry error” and describe precisely which atom, charge or angle needs checking.",
  "feedback.categoryLabel": "Feedback type",
  "feedback.category.usefulness": "Usefulness",
  "feedback.category.clarity": "Clarity",
  "feedback.category.chemistryError": "Suspected chemistry error",
  "feedback.category.other": "Other",
  "feedback.commentLabel": "Note (do not enter a name or student ID)",
  "feedback.submitting": "Submitting…",
  "feedback.submit": "Submit anonymous feedback",
  "feedback.rating.legend": "Usefulness (1–5)",

  // Molecule search
  "moleculeSearch.label": "Search by name or formula",
  "moleculeSearch.placeholder": "Enter at least 2 characters",

  // Lewis
  "lewis.formalCharge.caption": "Formal charge per atom",
  "lewis.formalCharge.atom": "Atom",
  "lewis.formalCharge.lonePairs": "Lone pairs",
  "lewis.formalCharge.charge": "Charge",
  "lewis.svgAria": "Lewis structure",
  "lewis.totalValence": "Total valence electrons",
  "lewis.source": "Structure source",
  "lewis.showFormalCharge": "Show formal charge",
  "lewis.resonance.forms": "{forms} equivalent resonance structures",

  // Properties
  "property.source.curated": "Curated data",
  "property.source.computed": "Computed value",
  "property.source.pubchem": "PubChem reference",
  "pubchem.title": "Structure reference",
  "pubchem.noCid": "No CID linked yet because source verification is not complete. No fabricated data is shown.",
  "teachingNote.title": "Learning tip",

  // 3D viewer
  "viewer3d.atomLabels": "Atom labels",
  "viewer3d.viewerAria": "Interactive 3D molecular model",
  "viewer3d.help": "Drag to rotate · scroll/pinch to zoom · touch supported.",
  "viewer3d.styleLabel": "Display style",
  "viewer3d.style.stick": "Ball and stick",
  "viewer3d.style.sphere": "Space filling",
  "viewer3d.fallback": "The browser could not initialize WebGL. You can still learn from the Lewis structure and the VSEPR table.",
  "viewer3d.reset": "Reset",
  "viewer3d.fullscreen": "Fullscreen",

  // VSEPR
  "vsepr.badgeAria": "VSEPR notation {notation}",
  "vsepr.domain.bonding": "Bonding domains",
  "vsepr.domain.lonePairs": "Lone pairs",
  "vsepr.domain.steric": "Total domains",
  "vsepr.notationHint": "Count the domains around the central atom; a multiple bond still counts as one domain.",
  "vsepr.electronGeometry": "Electron-domain geometry",
  "vsepr.molecularGeometry": "Molecular geometry",
  "vsepr.pedagogicalLabel": "Pedagogical label:",

  // Workflow
  "workflow.summary.substance": "Substance",
  "workflow.summary.classification": "Classification",
  "workflow.summary.geometry": "Geometry",
  "workflow.summary.bonds": "bonds",
  "workflow.summary.lonePairs": "lone pairs",
  "workflow.stepper.aria": "Analysis workflow",
  "workflow.step.input": "Input",
  "workflow.step.lewis": "Lewis",
  "workflow.step.axen": "AXnEm",
  "workflow.step.geometry": "Geometry",
  "workflow.step.model3d": "3D model",
  "workflow.step.explanation": "Explanation",

  // API errors
  "api.error.timeout": "The request timed out. Please try again.",
  "api.error.network": "Could not connect to the server. The examples need the backend running locally.",
};

const catalogues: Record<Lang, Catalogue> = { vi, en };

/** Resolve a translation key for a language, interpolating `{param}` placeholders. */
export function translate(lang: Lang, key: string, params?: Record<string, string | number>): string {
  const table = catalogues[lang] || catalogues[DEFAULT_LANG];
  let value = table[key] ?? catalogues[DEFAULT_LANG][key] ?? key;
  if (params) {
    for (const [name, replacement] of Object.entries(params)) {
      value = value.replace(new RegExp(`\\{${name}\\}`, "g"), String(replacement));
    }
  }
  return value;
}
