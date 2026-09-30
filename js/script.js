(function () {
  "use strict";

  // Marca que o JavaScript carregou — a partir daqui a animação de
  // entrada (.reveal) passa a valer. Se o JS falhar mais abaixo por
  // qualquer motivo, o conteúdo já está visível por padrão (ver
  // css/style.css) e nunca fica "sumido" na tela.
  document.documentElement.classList.add("js-ready");

  /* ============================================================
     Configuração — altere o número de WhatsApp aqui
     ============================================================ */
  var WHATSAPP_NUMBER = "5511975548090"; // (11) 97554-8090
  var WHATSAPP_MESSAGE = "Olá! Gostaria de falar com a Telemais sobre regularização da minha empresa.";

  function buildWhatsappUrl() {
    return "https://wa.me/" + WHATSAPP_NUMBER + "?text=" + encodeURIComponent(WHATSAPP_MESSAGE);
  }

  document.querySelectorAll(".js-whatsapp-link").forEach(function (link) {
    link.setAttribute("href", buildWhatsappUrl());
    link.setAttribute("target", "_blank");
    link.setAttribute("rel", "noopener");
  });

  /* ============================================================
     Header: fundo branco ao rolar
     ============================================================ */
  var header = document.getElementById("site-header");
  var SCROLL_THRESHOLD = 40;

  function updateHeaderState() {
    if (window.scrollY > SCROLL_THRESHOLD) {
      header.classList.add("is-scrolled");
    } else {
      header.classList.remove("is-scrolled");
    }
  }
  updateHeaderState();
  window.addEventListener("scroll", updateHeaderState, { passive: true });

  /* ============================================================
     Menu mobile
     ============================================================ */
  var hamburger = document.getElementById("hamburger");
  var mobileNav = document.getElementById("mobile-nav");

  function closeMobileNav() {
    hamburger.classList.remove("is-open");
    mobileNav.classList.remove("is-open");
    hamburger.setAttribute("aria-expanded", "false");
    document.body.style.overflow = "";
  }

  function toggleMobileNav() {
    var isOpen = mobileNav.classList.toggle("is-open");
    hamburger.classList.toggle("is-open", isOpen);
    hamburger.setAttribute("aria-expanded", String(isOpen));
    document.body.style.overflow = isOpen ? "hidden" : "";
  }

  hamburger.addEventListener("click", toggleMobileNav);
  mobileNav.querySelectorAll("a").forEach(function (link) {
    link.addEventListener("click", closeMobileNav);
  });

  /* ============================================================
     Scroll reveal (IntersectionObserver)
     ============================================================ */
  var revealEls = document.querySelectorAll(".reveal");

  if ("IntersectionObserver" in window) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    revealEls.forEach(function (el) { observer.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add("is-visible"); });
  }

  /* ============================================================
     Formulário de diagnóstico — validação e envio
     ============================================================ */
  var form = document.getElementById("diagnostic-form");
  var formCard = document.getElementById("form-card");
  var formSuccess = document.getElementById("form-success");

  var requiredFields = ["nome", "empresa", "whatsapp", "tipoNegocio", "cidade"];

  function setError(fieldName, hasError) {
    var wrapper = form.querySelector('[data-field="' + fieldName + '"]');
    if (!wrapper) return;
    wrapper.classList.toggle("has-error", hasError);
  }

  function isValidEmail(value) {
    if (!value) return true; // e-mail é opcional
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
  }

  function isValidPhone(value) {
    var digits = value.replace(/\D/g, "");
    return digits.length >= 10;
  }

  function validateForm() {
    var valid = true;

    requiredFields.forEach(function (name) {
      var input = form.elements[name];
      var value = input ? input.value.trim() : "";
      var fieldValid = value.length > 0;

      if (name === "whatsapp" && fieldValid) {
        fieldValid = isValidPhone(value);
      }

      setError(name, !fieldValid);
      if (!fieldValid) valid = false;
    });

    var emailInput = form.elements["email"];
    var emailValid = isValidEmail(emailInput.value.trim());
    setError("email", !emailValid);
    if (!emailValid) valid = false;

    return valid;
  }

  if (form) {
    form.addEventListener("submit", async function (e) {
      e.preventDefault();

      if (!validateForm()) {
        var firstError = form.querySelector(".has-error input, .has-error select");
        if (firstError) firstError.focus();
        return;
      }

      var submitBtn = form.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      submitBtn.textContent = "Enviando...";

      var needs = Array.prototype.slice.call(form.querySelectorAll('input[name="necessidade"]:checked'))
        .map(function (el) { return el.value; });
      var funcionando = form.querySelector('input[name="funcionando"]:checked');

      var payload = {
        name: form.elements["nome"].value.trim(),
        company_name: form.elements["empresa"].value.trim(),
        phone: form.elements["whatsapp"].value.trim(),
        email: form.elements["email"].value.trim() || null,
        business_type: form.elements["tipoNegocio"].value.trim(),
        city: form.elements["cidade"].value.trim(),
        operating_status: funcionando ? funcionando.value : null,
        needs: needs,
        description: form.elements["descricao"].value.trim() || null,
        source: "site"
      };

      try {
        if (window.supabaseClient) {
          var { error } = await window.supabaseClient.from("leads").insert(payload);
          if (error) throw error;
        }
        form.style.display = "none";
        formSuccess.classList.add("is-visible");
        formCard.scrollIntoView({ behavior: "smooth", block: "center" });
      } catch (err) {
        console.error("Erro ao enviar diagnóstico:", err);
        submitBtn.disabled = false;
        submitBtn.textContent = "Solicitar análise";
        alert("Não foi possível enviar agora. Tente novamente em instantes ou fale pelo WhatsApp.");
      }
    });

    // Remove o erro assim que o campo é corrigido
    requiredFields.concat(["email"]).forEach(function (name) {
      var input = form.elements[name];
      if (!input) return;
      input.addEventListener("input", function () {
        setError(name, false);
      });
    });
  }

  var partnerForm = document.getElementById("partner-interest-form");
  var openPartnerForm = document.getElementById("btn-open-partner-form");
  var closePartnerForm = document.getElementById("btn-close-partner-form");
  if (openPartnerForm && partnerForm) openPartnerForm.addEventListener("click", function () { partnerForm.hidden = false; partnerForm.classList.add("is-visible"); partnerForm.scrollIntoView({ behavior: "smooth", block: "center" }); partnerForm.elements.name.focus(); });
  if (closePartnerForm && partnerForm) closePartnerForm.addEventListener("click", function () { partnerForm.hidden = true; openPartnerForm.focus(); });
  if (partnerForm) partnerForm.addEventListener("submit", async function (e) {
    e.preventDefault(); var button = partnerForm.querySelector("button"), message = document.getElementById("partner-interest-message");
    button.disabled = true; button.textContent = "Enviando...";
    var f = partnerForm.elements, payload = { name:f.name.value.trim(), company_name:f.company.value.trim() || null, phone:f.phone.value.trim(), email:f.email.value.trim(), city:f.city.value.trim() || null, business_type:f.specialty.value, description:f.description.value.trim() || null, source:"site_parceria", status:"new" };
    var result = await window.supabaseClient.from("leads").insert(payload);
    if (result.error) { message.textContent="Não foi possível enviar agora. Tente novamente."; button.disabled=false; button.textContent="Solicitar cadastro de parceria"; return; }
    partnerForm.reset(); message.textContent="Cadastro recebido! A Telemais entrará em contato."; button.textContent="Cadastro enviado";
  });
})();
