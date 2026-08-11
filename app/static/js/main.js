(function () {
  "use strict";

  // ---------- Theme toggle ----------
  var root = document.documentElement;
  var themeToggle = document.getElementById("themeToggle");

  function currentTheme() {
    return root.getAttribute("data-theme") || "light";
  }

  function setTheme(theme) {
    root.setAttribute("data-theme", theme);
    localStorage.setItem("haven-theme", theme);
  }

  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      setTheme(currentTheme() === "dark" ? "light" : "dark");
    });
  }

  // ---------- Mobile nav ----------
  var navToggle = document.getElementById("navToggle");
  var siteNav = document.getElementById("siteNav");

  if (navToggle && siteNav) {
    navToggle.addEventListener("click", function () {
      var isOpen = siteNav.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });
  }

  // ---------- Auto-dismiss flash messages ----------
  var flashStack = document.getElementById("flashStack");
  if (flashStack) {
    setTimeout(function () {
      flashStack.querySelectorAll(".flash").forEach(function (el) {
        el.style.transition = "opacity 0.4s ease";
        el.style.opacity = "0";
        setTimeout(function () { el.remove(); }, 400);
      });
    }, 6000);
  }

  // ---------- Image preview on upload forms ----------
  var imageInput = document.querySelector('input[type="file"][name="image"]');
  var previewImg = document.getElementById("imagePreview");
  if (imageInput && previewImg) {
    imageInput.addEventListener("change", function () {
      var file = imageInput.files && imageInput.files[0];
      if (file) {
        previewImg.src = URL.createObjectURL(file);
        previewImg.style.display = "block";
      }
    });
  }
})();
