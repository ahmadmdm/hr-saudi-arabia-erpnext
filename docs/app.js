const orbitData = {
  contract: { code: 'SEC / 01', kicker: 'البداية الموثقة', title: 'العقد', copy: 'نوع العلاقة، الأجر، المدة، التجربة والالتزامات في مرجع واحد.', status: 'موثق' },
  attendance: { code: 'SEC / 02', kicker: 'إيقاع العمل', title: 'الحضور', copy: 'وردية وموقع ودخول وخروج وغياب يتحول إلى سجل يومي وشهري.', status: 'متصل' },
  leave: { code: 'SEC / 03', kicker: 'الاستحقاق المرن', title: 'الإجازات', copy: 'سياسة عامة أو تخصيص للقسم والموظف مع حدود نظامية محفوظة.', status: 'محسوب' },
  payroll: { code: 'SEC / 04', kicker: 'الاستحقاق المالي', title: 'الراتب', copy: 'راتب وتسويات وقروض وتأمينات وحماية أجور في دورة شهرية واحدة.', status: 'جاهز' },
  compliance: { code: 'SEC / 05', kicker: 'الأثر القابل للتدقيق', title: 'الامتثال', copy: 'مهل وتنبيهات وإجراءات وأدلة تربط كل التزام بالمسؤول والموعد.', status: 'مراقب' },
  exit: { code: 'SEC / 06', kicker: 'النهاية المنضبطة', title: 'الخروج', copy: 'إنهاء وإخلاء ومقابلة ومخالصة ومكافأة نهاية خدمة دون فجوات.', status: 'مغلق' }
};

const journeyData = {
  hire: { number: '01', label: 'قرار التوظيف', title: 'من الاحتياج إلى مرشح جاهز للعقد.', copy: 'طلب توظيف واضح، مرشحون، مقابلات، قرار موثق، ثم انتقال منضبط إلى إنشاء العقد دون إعادة إدخال البيانات.', output: 'طلب توظيف · تقييم مرشح · قرار قبول' },
  join: { number: '02', label: 'الانضمام المنظم', title: 'كل ما يحتاجه اليوم الأول، قبل أن يبدأ.', copy: 'عقد وتهيئة ووثائق وفترة تجربة ومسؤوليات واضحة، مع ملف موظف يجمع الصورة بدل توزيعها.', output: 'عقد نشط · ملف مكتمل · خطة تهيئة' },
  work: { number: '03', label: 'التشغيل اليومي', title: 'الحضور والإجازة والراتب يتحدثون لغة واحدة.', copy: 'الوردية والموقع والحركة اليومية والاستحقاق وسياسة الإجازة تنتهي إلى راتب يمكن تفسيره ومراجعته.', output: 'حضور شهري · رصيد إجازة · مسير راتب' },
  grow: { number: '04', label: 'النمو والعلاقات', title: 'الترقية والأداء والملاحظة لا تضيع في البريد.', copy: 'تقييمات وتنقلات وترقيات وإنذارات وتظلمات وتحقيقات ضمن تسلسل يحفظ القرار والدليل.', output: 'قرار وظيفي · سجل أداء · أثر علاقة عمل' },
  govern: { number: '05', label: 'الحوكمة والامتثال', title: 'كل التزام له مالك وموعد ودليل.', copy: 'مركز متابعة للوائح والسجلات والتفتيش والإفصاحات والتصاريح والتنبيهات المرتبطة بمسؤول واضح.', output: 'إجراء امتثال · مهلة · دليل إغلاق' },
  close: { number: '06', label: 'إغلاق العلاقة', title: 'نهاية خدمة لا تترك سؤالًا مفتوحًا.', copy: 'الإنهاء والإخلاء والمقابلة والمستحقات ومكافأة نهاية الخدمة والمخالصة في مسار واحد قابل للمراجعة.', output: 'إخلاء طرف · EOSB · مخالصة نهائية' }
};

const roleData = {
  admin: {
    code: 'SYS.ADMIN', heading: 'أطلق بيئة موثوقة.', intro: 'ابدأ من بنية صحيحة، ثم ثبّت التطبيق واضبط الصلاحيات والنسخ الاحتياطي قبل إدخال بيانات حقيقية.',
    steps: [
      ['تهيئة البيئة', 'تحقق من Frappe وERPNext والفرع المطابق.'],
      ['تثبيت Saudi HR', 'ثبّت التطبيق، نفّذ migrate وابنِ الأصول.'],
      ['توزيع الصلاحيات', 'افصل مدير النظام وHR والرواتب والخدمة الذاتية.'],
      ['اختبار الاستعادة', 'خذ نسخة احتياطية ونفّذ استعادة تجريبية موثقة.']
    ]
  },
  hr: {
    code: 'HR.OPERATE', heading: 'ابنِ التشغيل قبل البيانات.', intro: 'عرّف الهيكل والسياسات أولًا، ثم أضف مجموعة تجريبية وشغّل عليها دورة موظف كاملة.',
    steps: [
      ['الهيكل التنظيمي', 'شركة وفروع وأقسام ووظائف ومواقع حضور.'],
      ['السياسات الأساسية', 'ورديات وإجازات وعقود وتنبيهات صلاحية.'],
      ['ملف موظف تجريبي', 'هوية وعقد ووثائق وبيانات راتب وصلاحيات.'],
      ['دورة يومية كاملة', 'حضور وإجازة وموافقة وراتب ثم مراجعة التقارير.']
    ]
  },
  quality: {
    code: 'QA.ACCEPT', heading: 'اثبت أن الدورة تعمل.', intro: 'اختبر السلوك والنتيجة والصلاحية والواجهة على بيانات تجريبية قبل توسيع النطاق.',
    steps: [
      ['اختبار المسار السعيد', 'نفّذ كل دورة من البداية إلى المخرج المتوقع.'],
      ['اختبار الحدود', 'تواريخ متداخلة وصلاحيات ناقصة وحسابات قصوى.'],
      ['اختبار العربية والجوال', 'RTL وتجاوب ولوحة مفاتيح وحالات فارغة.'],
      ['قرار الإطلاق', 'وثّق الأدلة والملاحظات وخطة الرجوع والاستعادة.']
    ]
  }
};

const $ = (selector, scope = document) => scope.querySelector(selector);
const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;

requestAnimationFrame(() => document.body.classList.add('page-ready'));

const menuToggle = $('[data-menu-toggle]');
const menuOverlay = $('[data-menu-overlay]');
function setMenu(open) {
  menuToggle.classList.toggle('is-open', open);
  menuToggle.setAttribute('aria-expanded', String(open));
  menuToggle.setAttribute('aria-label', open ? 'إغلاق القائمة' : 'فتح القائمة');
  menuOverlay.classList.toggle('is-open', open);
  menuOverlay.setAttribute('aria-hidden', String(!open));
  document.body.style.overflow = open ? 'hidden' : '';
}
menuToggle.addEventListener('click', () => setMenu(!menuOverlay.classList.contains('is-open')));
$$('a', menuOverlay).forEach((link) => link.addEventListener('click', () => setMenu(false)));

const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (!entry.isIntersecting) return;
    entry.target.classList.add('is-visible');
    revealObserver.unobserve(entry.target);
  });
}, { threshold: .12 });
$$('.reveal').forEach((item) => revealObserver.observe(item));

const orbitNodes = $$('[data-orbit-node]');
const employeeCore = $('.employee-core');
let orbitIndex = 0;
let orbitTimer;
function selectOrbit(key, userInitiated = false) {
  const data = orbitData[key];
  if (!data) return;
  employeeCore.classList.remove('is-changing');
  void employeeCore.offsetWidth;
  employeeCore.classList.add('is-changing');
  $('[data-orbit-code]').textContent = data.code;
  $('[data-orbit-kicker]').textContent = data.kicker;
  $('[data-orbit-title]').textContent = data.title;
  $('[data-orbit-copy]').textContent = data.copy;
  $('[data-orbit-status]').textContent = data.status;
  orbitNodes.forEach((node, index) => {
    const active = node.dataset.orbitNode === key;
    node.classList.toggle('is-active', active);
    node.setAttribute('aria-pressed', String(active));
    if (active) orbitIndex = index;
  });
  if (userInitiated) restartOrbit();
}
function restartOrbit() {
  clearInterval(orbitTimer);
  if (!reducedMotion) orbitTimer = setInterval(() => {
    orbitIndex = (orbitIndex + 1) % orbitNodes.length;
    selectOrbit(orbitNodes[orbitIndex].dataset.orbitNode);
  }, 4200);
}
orbitNodes.forEach((node) => node.addEventListener('click', () => selectOrbit(node.dataset.orbitNode, true)));
$('[data-orbit-stage]').addEventListener('mouseenter', () => clearInterval(orbitTimer));
$('[data-orbit-stage]').addEventListener('mouseleave', restartOrbit);
restartOrbit();

const journeyTabs = $$('[data-journey]');
const journeyPanel = $('.journey-ledger__panel');
function selectJourney(key) {
  const data = journeyData[key];
  if (!data) return;
  journeyTabs.forEach((tab) => tab.setAttribute('aria-selected', String(tab.dataset.journey === key)));
  journeyPanel.classList.remove('is-changing');
  void journeyPanel.offsetWidth;
  journeyPanel.classList.add('is-changing');
  $('[data-journey-number]').textContent = data.number;
  $('[data-journey-label]').textContent = data.label;
  $('[data-journey-title]').textContent = data.title;
  $('[data-journey-copy]').textContent = data.copy;
  $('[data-journey-output]').textContent = data.output;
}
journeyTabs.forEach((tab) => tab.addEventListener('click', () => selectJourney(tab.dataset.journey)));

const roleTabs = $$('[data-role]');
const roleSteps = $('[data-role-steps]');
function renderRole(key) {
  const data = roleData[key];
  roleTabs.forEach((tab) => tab.setAttribute('aria-selected', String(tab.dataset.role === key)));
  $('[data-role-code]').textContent = data.code;
  $('[data-role-heading]').textContent = data.heading;
  $('[data-role-intro]').textContent = data.intro;
  $('[data-role-step-total]').textContent = data.steps.length;
  $('[data-role-step-current]').textContent = '1';
  $('[data-role-progress]').style.transform = 'scaleX(.25)';
  roleSteps.innerHTML = data.steps.map((step, index) => `<button type="button" class="tutorial-step${index === 0 ? ' is-current' : ''}" data-step="${index}"><span>${String(index + 1).padStart(2, '0')}</span><div><b>${step[0]}</b><small>${step[1]}</small></div><i></i></button>`).join('');
  roleSteps.classList.remove('is-changing');
  void roleSteps.offsetWidth;
  roleSteps.classList.add('is-changing');
  $$('[data-step]', roleSteps).forEach((step) => step.addEventListener('click', () => {
    $$('[data-step]', roleSteps).forEach((item) => item.classList.toggle('is-current', item === step));
    const current = Number(step.dataset.step) + 1;
    $('[data-role-step-current]').textContent = current;
    $('[data-role-progress]').style.transform = `scaleX(${current / data.steps.length})`;
  }));
}
roleTabs.forEach((tab) => tab.addEventListener('click', () => renderRole(tab.dataset.role)));
renderRole('admin');

const versionButtons = $$('[data-version]');
const versionDial = $('.version-dial');
versionButtons.forEach((button) => button.addEventListener('click', () => {
  const branch = `version-${button.dataset.version}`;
  versionButtons.forEach((item) => {
    const active = item === button;
    item.classList.toggle('is-active', active);
    item.setAttribute('aria-pressed', String(active));
  });
  versionDial.classList.toggle('is-v16', button.dataset.version === '16');
  $('[data-branch]').textContent = branch;
  $('[data-branch-label]').textContent = branch;
}));

const toast = $('[data-toast]');
let toastTimer;
function showToast(message) {
  toast.textContent = message;
  toast.classList.add('is-visible');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('is-visible'), 2200);
}
$('[data-copy]').addEventListener('click', async () => {
  const commands = $('[data-install-code]').innerText;
  try {
    await navigator.clipboard.writeText(commands);
    showToast('نُسخت أوامر التثبيت');
  } catch {
    const area = document.createElement('textarea');
    area.value = commands;
    area.style.position = 'fixed';
    area.style.opacity = '0';
    document.body.append(area);
    area.select();
    const copied = document.execCommand('copy');
    area.remove();
    showToast(copied ? 'نُسخت أوامر التثبيت' : 'حدد الأوامر وانسخها يدويًا');
  }
});

$('[data-year]').textContent = new Date().getFullYear();
